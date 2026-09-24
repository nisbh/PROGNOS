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
    };
}

# Add state to connection record
redef record connection += {
    prognos_info: Info &optional;
    
    # Trackers for averages
    sum_win_orig: count &default=0;
    sum_win_resp: count &default=0;
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
        
        if ( is_orig ) {
            if ( ! c$prognos_info?$min_ttl_orig || ttl < c$prognos_info$min_ttl_orig )
                c$prognos_info$min_ttl_orig = ttl;
            if ( ! c$prognos_info?$max_ttl_orig || ttl > c$prognos_info$max_ttl_orig )
                c$prognos_info$max_ttl_orig = ttl;
        } else {
            if ( ! c$prognos_info?$min_ttl_resp || ttl < c$prognos_info$min_ttl_resp )
                c$prognos_info$min_ttl_resp = ttl;
            if ( ! c$prognos_info?$max_ttl_resp || ttl > c$prognos_info$max_ttl_resp )
                c$prognos_info$max_ttl_resp = ttl;
        }
    } else if ( p?$ip6 ) {
        is_orig = (p$ip6$src == c$id$orig_h);
    }
    
    if ( p?$tcp ) {
        local win = p$tcp$win;
        if ( is_orig ) {
            c$sum_win_orig += win;
        } else {
            c$sum_win_resp += win;
        }
    }
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
    
    Log::write(PROGNOS::LOG, info);
}
