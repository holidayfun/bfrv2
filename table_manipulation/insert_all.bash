cli.py -s 1 < entries_s1
cli.py -s 2 < entries_s2
cli.py -s 3 < entries_s3

cli.py -s 1 < bier_ingress
cli.py -s 2 < bier_ingress
cli.py -s 3 < bier_ingress

cli.py -s 1 < find_pos
cli.py -s 2 < find_pos
cli.py -s 3 < find_pos


cli.py -s 1 < bift_entries_s1
cli.py -s 2 < bift_entries_s2
cli.py -s 3 < bift_entries_s3

cli.py -s 1 < check_bfr_id_entries_s1
cli.py -s 2 < check_bfr_id_entries_s2
cli.py -s 3 < check_bfr_id_entries_s3

cli.py -s 1 < do_clone_recirculation_table
cli.py -s 1 < do_cloning_table
cli.py -s 1 < mirroring

cli.py -s 2 < do_clone_recirculation_table
cli.py -s 2 < do_clone_recirculation_table
cli.py -s 2 < do_cloning_table

cli.py -s 3 < mirroring
cli.py -s 3 < do_cloning_table
cli.py -s 3 < mirroring
