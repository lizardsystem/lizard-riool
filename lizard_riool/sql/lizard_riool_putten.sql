-- View: lizard_riool_putten

-- DROP VIEW lizard_riool_putten;

CREATE OR REPLACE VIEW lizard_riool_putten AS 
        (         SELECT lizard_riool_riool.upload_id, lizard_riool_riool.aad AS put_id, lizard_riool_riool.aae AS the_geom
                   FROM lizard_riool_riool
        UNION 
                 SELECT lizard_riool_riool.upload_id, lizard_riool_riool.aaf AS put_id, lizard_riool_riool.aag AS the_geom
                   FROM lizard_riool_riool)
UNION 
         SELECT lizard_riool_put.upload_id, lizard_riool_put.caa AS put_id, lizard_riool_put.cab AS the_geom
           FROM lizard_riool_put;

ALTER TABLE lizard_riool_putten OWNER TO buildout;


