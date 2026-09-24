module PROGNOS;

export {
    redef enum Log::ID += { LOG };

    type Info: record {
        ts: time &log;
        uid: string &log;
        id: conn_id &log;
        proto: transport_proto &log;
        service: string &log &optional;
        duration: interval &log &optional;
        orig_bytes: count &log &optional;
        resp_bytes: count &log &optional;
        orig_pkts: count &log &optional;
        resp_pkts: count &log &optional;
        
        # Packet-level features
        min_ttl_orig: count &log &optional;
        max_ttl_orig: count &log &optional;
        min_ttl_resp: count &log &optional;
        max_ttl_resp: count &log &optional;
        avg_win_orig: double &log &optional;
        avg_win_resp: double &log &optional;
        
        # New packet-level features for PS
        payload_min_orig: count &log &optional;
        payload_max_orig: count &log &optional;
        payload_min_resp: count &log &optional;
        payload_max_resp: count &log &optional;
        
        frag_count: count &log &default=0;
        retrans_orig: count &log &default=0;
        retrans_resp: count &log &default=0;
        
        # TCP Flag Bitmasks (Counts)
        flag_syn: count &log &default=0;
        flag_ack: count &log &default=0;
        flag_fin: count &log &default=0;
        flag_rst: count &log &default=0;
        flag_psh: count &log &default=0;
        flag_urg: count &log &default=0;
        
        # IAT (Inter-Arrival Time) Statistics
        iat_mean: double &log &default=0.0;
        iat_max: double &log &default=0.0;
        iat_var: double &log &default=0.0;
    };
}

# Add state to connection record
redef record connection += {
    prognos_info: Info &optional;
    
    # Trackers for averages and IAT
    sum_win_orig: count &default=0;
    sum_win_resp: count &default=0;
    
    last_pkt_time: time &optional;
    iat_sum: double &default=0.0;
    iat_sq_sum: double &default=0.0;
    iat_max: double &default=0.0;
    iat_count: count &default=0;
};

event zeek_init() {
    Log::create_stream(PROGNOS::LOG, [$columns=Info, $path="prognos_features"]);
}

event new_connection(c: connection) {
    local info: Info;
    info$ts = c$start_time;
    info$uid = c$uid;
    info$id = c$id;
    
    c$prognos_info = info;
}

event new_packet(c: connection, p: pkt_hdr) {
    if ( ! c?$prognos_info ) return;
    
    local is_orig = F;
    if ( p?$ip ) {
        is_orig = (p$ip$src == c$id$orig_h);
        local ttl = p$ip$ttl;
        local pkt_len = p$ip$len;
        
        if ( p$ip?$mf && p$ip$mf ) {
            c$prognos_info$frag_count += 1;
        }
        
        if ( is_orig ) {
            if ( ! c$prognos_info?$min_ttl_orig || ttl < c$prognos_info$min_ttl_orig )
                c$prognos_info$min_ttl_orig = ttl;
            if ( ! c$prognos_info?$max_ttl_orig || ttl > c$prognos_info$max_ttl_orig )
                c$prognos_info$max_ttl_orig = ttl;
                
            if ( ! c$prognos_info?$payload_min_orig || pkt_len < c$prognos_info$payload_min_orig )
                c$prognos_info$payload_min_orig = pkt_len;
            if ( ! c$prognos_info?$payload_max_orig || pkt_len > c$prognos_info$payload_max_orig )
                c$prognos_info$payload_max_orig = pkt_len;
        } else {
            if ( ! c$prognos_info?$min_ttl_resp || ttl < c$prognos_info$min_ttl_resp )
                c$prognos_info$min_ttl_resp = ttl;
            if ( ! c$prognos_info?$max_ttl_resp || ttl > c$prognos_info$max_ttl_resp )
                c$prognos_info$max_ttl_resp = ttl;
                
            if ( ! c$prognos_info?$payload_min_resp || pkt_len < c$prognos_info$payload_min_resp )
                c$prognos_info$payload_min_resp = pkt_len;
            if ( ! c$prognos_info?$payload_max_resp || pkt_len > c$prognos_info$payload_max_resp )
                c$prognos_info$payload_max_resp = pkt_len;
        }
    } else if ( p?$ip6 ) {
        is_orig = (p$ip6$src == c$id$orig_h);
    }
    
    if ( p?$tcp ) {
        local win = p$tcp$win;
        local flags = p$tcp$flags;
        
        if ( (flags & 0x02) != 0 ) c$prognos_info$flag_syn += 1;
        if ( (flags & 0x10) != 0 ) c$prognos_info$flag_ack += 1;
        if ( (flags & 0x01) != 0 ) c$prognos_info$flag_fin += 1;
        if ( (flags & 0x04) != 0 ) c$prognos_info$flag_rst += 1;
        if ( (flags & 0x08) != 0 ) c$prognos_info$flag_psh += 1;
        if ( (flags & 0x20) != 0 ) c$prognos_info$flag_urg += 1;
        
        if ( is_orig ) {
            c$sum_win_orig += win;
        } else {
            c$sum_win_resp += win;
        }
    }
    
    # IAT Calculation
    local current_time = network_time();
    if ( c?$last_pkt_time ) {
        local iat = interval_to_double(current_time - c$last_pkt_time);
        c$iat_sum += iat;
        c$iat_sq_sum += (iat * iat);
        c$iat_count += 1;
        if ( iat > c$iat_max ) c$iat_max = iat;
    }
    c$last_pkt_time = current_time;
}

event connection_state_remove(c: connection) {
    if ( ! c?$prognos_info ) return;
    
    local info = c$prognos_info;
    info$proto = get_port_transport_proto(c$id$resp_p);
    info$service = c?$service ? join_string_set(c$service, ",") : "-";
    
    if ( c?$duration ) info$duration = c$duration;
    if ( c?$orig ) {
        info$orig_bytes = c$orig$size;
        info$orig_pkts = c$orig$num_pkts;
        if ( info$orig_pkts > 0 )
            info$avg_win_orig = (c$sum_win_orig + 0.0) / info$orig_pkts;
    }
    if ( c?$resp ) {
        info$resp_bytes = c$resp$size;
        info$resp_pkts = c$resp$num_pkts;
        if ( info$resp_pkts > 0 )
            info$avg_win_resp = (c$sum_win_resp + 0.0) / info$resp_pkts;
    }
    
    # Finalize IAT stats
    if ( c$iat_count > 0 ) {
        info$iat_mean = c$iat_sum / c$iat_count;
        info$iat_max = c$iat_max;
        local variance = (c$iat_sq_sum / c$iat_count) - (info$iat_mean * info$iat_mean);
        info$iat_var = variance > 0.0 ? variance : 0.0;
    }
    
    if ( c?$history ) {
        if ( "t" in c$history ) info$retrans_orig = 1;
        if ( "T" in c$history ) info$retrans_resp = 1;
    }
    
    Log::write(PROGNOS::LOG, info);
}
