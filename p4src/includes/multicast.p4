
metadata intrinsic_metadata_t intrinsic_metadata;
table multicast_assoc {
    reads {
        ipv4.dstAddr : exact;
    }
    actions {
        set_mc_group;
        _drop;
    }
}

action set_mc_group(group_id) {
    modify_field(intrinsic_metadata.mcast_grp, group_id);
}
                                                                            table send_mc {
    reads {
        intrinsic_metadata.mcast_grp : exact;
        standard_metadata.egress_port: exact;
        ipv4.dstAddr : exact;
    }
    actions {
        set_receiver;
        _drop;
    }
    size:256;
}

action set_receiver(ip, dmac) {
    modify_field(ipv4.dstAddr, ip);
    modify_field(ethernet.dstAddr, dmac);    
}

