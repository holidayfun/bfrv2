header_type intrinsic_metadata_t {
    fields {
        mcast_grp : 4;
        egress_rid : 4;
        mcast_hash : 16;
        recirculate_flag : 1;
        resubmit_flag : 1;
        pad : 6;
    }
}

header_type routing_metadata_t {
    fields 
    {
        nhop_ipv4 : 32;
    }
}            

header_type bier_metadata_t {
    fields 
    {         
        k_pos : 6;
        bs_remaining: 16;
        needs_cloning : 1;
        decap : 1;
    }
}

header_type bier_t {
  fields {
    first_nibble : 4;
    Ver : 4;
    Len : 4;
    Entropy : 20;
    BitString : 16;
    OAM : 2;
    Reserved : 10;
    Proto : 4;
    BFIR_id : 16;
  }
  /* For now use fixed length BitString

  Length of 2^(Len + 5) = 2 << (Len + 4) bits of BitString + 64 Bit for other fields
  length : ((2 << (Len + 4)) + 64) ;
  max_length : 4160;
  */
}

header_type ethernet_t {
  fields {
    dstAddr : 48;
    srcAddr : 48;
    etherType : 16;
  }
}

header_type ipv4_t {
  fields {
    version : 4;
    ihl : 4;
    diffserv : 8;
    totalLen : 16;
    identification : 16;
    flags : 3;
    fragOffset : 13;
    ttl : 8;
    protocol : 8;
    hdrChecksum : 16;
    srcAddr : 32;
    dstAddr : 32;
  }
}
