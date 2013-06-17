"""Helper functions used by the "process uploaded file" task."""

import math
import os.path

from django.contrib.gis.geos import LineString, Point

from sufriblib.errors import Error
from sufriblib import util

from . import models


def get_puts(ribfile, riberrors):
    """Returns a dictionary {putid: putinfo} where putinfo has is
    itself a dictionary with the following keys:

    - line_number
    - putid
    - coordinate, as a WGS84 Point
    - is_sink, boolean
    - surface level, m above NAP

    Errors (sufriblib.errors.Error objects) are appended to riberrors.
    """

    putdict = dict()
    found_first_sink = False

    for putline in ribfile.lines_of_type("*PUT"):
        putid = putline.putid  # Existence is already checked in sufriblib
        if not putid:
            continue  # So no need to report here, just skip

        if putid in putdict:
            riberrors.append(Error(
                    line_number=putline.line_number,
                    message=("Put referentie {putid} komt meerdere keren voor"
                             .format(putid=putid))))
            continue

        is_sink = putline.is_sink

        if is_sink:
            if found_first_sink:
                riberrors.append(Error(
                        line_number=putline.line_number,
                        message="Meer dan 1 put als gemaal gemarkeerd"))
            found_first_sink = True

        # putline.CCU is not a required field, but if it's there, it
        # must be a float. Otherwise we'll try to compute the surface
        # level later on.
        if putline.CCU and not putline.CCU.isspace():
            try:
                surface_level = float(putline.CCU)
            except ValueError:
                surface_level = None
                riberrors.append(Error(
                        line_number=putline.line_number,
                        message=(
                            "De waarde in veld CCU, '{ccu}', is geen "
                            "decimaal getal.").format(ccu=putline.CCU)))
        else:
            surface_level = None

        putdict[putid] = {
            'line_number': putline.line_number,
            'putid': putid,
            'coordinate': putline.wgs84_point,
            'rd_coordinate': putline.rd_point,
            'is_sink': is_sink,
            'surface_level': surface_level
            }

    return putdict


def get_sewers(ribfile, putdict, riberrors):
    """Returns the sewers. Uses putdict to check if puts mentioned
    actually exist. Appends errors to riberrors. Gets its data from
    *RIOO lines in the ribfile.

    Returned sewerdict is a dictionary {sewerid: sewerinfo} where
    sewerinfo is a dict with keys:
    - sewer_id
    - manhole_code_1
    - manhole_code_2
    - bob_1
    - bob_2
    - diameter
    - shape, either "circle" or "rectangle"
    """

    sewerdict = dict()

    for sewerline in ribfile.lines_of_type("*RIOO"):
        # Get bob1 from ACR
        if sewerline.ACR is None:
            riberrors.append(Error(
                    line_number=sewerline.line_number,
                    message=(
               "Veld ACR (BOB bij beginknoop absoluut) is niet ingevuld")))
            bob_1 = 0.0
        else:
            try:
                bob_1 = float(sewerline.ACR)
            except ValueError:
                bob_1 = 0.0
                riberrors.append(Error(
                        line_number=sewerline.line_number,
                        message=(
                            "Waarde ingevuld bij ACR (BOB bij beginknoop"
                            " absoluut), '{acr}', is geen decimaal getal")
                        .format(acr=sewerline.ACR)))

        # Get bob2 from ACS
        if sewerline.ACS is None:
            riberrors.append(Error(
                    line_number=sewerline.line_number,
                    message=(
               "Veld ACS (BOB bij eindknoop absoluut) is niet ingevuld")))
            bob_2 = 0.0
        else:
            try:
                bob_2 = float(sewerline.ACS)
            except ValueError:
                bob_2 = 0.0
                riberrors.append(Error(
                        line_number=sewerline.line_number,
                        message=(
                            "Waarde ingevuld bij ACS (BOB bij eindknoop"
                            " absoluut), '{acs}', is geen decimaal getal")
                        .format(acs=sewerline.ACS)))

        # Get diameter from ACB
        if sewerline.ACB is None:
            riberrors.append(Error(
                    line_number=sewerline.line_number,
                    message=(
               "Veld ACB (Hoogte) is niet ingevuld")))
            diameter = 0.0
        else:
            try:
                diameter = float(sewerline.ACB) / 1000.0  # mm
            except ValueError:
                diameter = 0.0
                riberrors.append(Error(
                        line_number=sewerline.line_number,
                        message=(
                            "Waarde ingevuld bij ACB (Hoogte)"
                            ", '{acb}', is geen decimaal getal")
                        .format(acb=sewerline.ACB)))

        if sewerline.manhole1_id not in putdict:
            manhole1_coordinate = sewerline.manhole1_wgs84_point

            if manhole1_coordinate is None:
                riberrors.append(Error(
                        line_number=sewerline.line_number,
                        message=(
                            "Knooppunt referentie {putcode} onbekend. "
                            "Komt niet voor in een *PUT regel en wordt "
                            "ook niet gedefinieerd in deze *RIOO regel.")
                        .format(putcode=sewerline.manhole1_id)))
            else:
                # Insert a new PUT defined in this RIOO line. Not sure if that
                # is allowed when there is at least one PUT line in the file,
                # but people do it in practice...
                putdict[sewerline.manhole1_id] = {
                    'line_number': sewerline.line_number,
                    'putid': sewerline.manhole1_id,
                    'coordinate': manhole1_coordinate,
                    'rd_coordinate': sewerline.manhole1_rd_point,
                    'is_sink': False,
                    'surface_level': None
                    }

        if sewerline.manhole2_id not in putdict:
            manhole2_coordinate = sewerline.manhole2_wgs84_point

            if manhole2_coordinate is None:
                riberrors.append(Error(
                        line_number=sewerline.line_number,
                        message=(
                            "Knooppunt referentie {putcode} onbekend. "
                            "Komt niet voor in een *PUT regel en wordt "
                            "ook niet gedefinieerd in deze *RIOO regel.")
                        .format(putcode=sewerline.manhole2_id)))
            else:
                # Insert a new PUT defined in this RIOO line. Not sure if that
                # is allowed when there is at least one PUT line in the file,
                # but people do it in practice...
                putdict[sewerline.manhole2_id] = {
                    'line_number': sewerline.line_number,
                    'putid': sewerline.manhole2_id,
                    'coordinate': manhole2_coordinate,
                    'rd_coordinate': sewerline.manhole2_rd_point,
                    'is_sink': False,
                    'surface_level': None
                    }

        sewerdict[sewerline.sewer_id] = {
            'sewer_id': sewerline.sewer_id,
            'manhole_code_1': sewerline.manhole1_id,
            'manhole_code_2': sewerline.manhole2_id,
            'bob_1': bob_1,
            'bob_2': bob_2,
            'diameter': diameter,
            'shape': "rectangle" if sewerline.ACA == "2" else "circle"
            }

    return sewerdict


def mrio_lines_by_sewer_id(rmbfile):
    lines = dict()

    for mrio_line in rmbfile.lines_of_type("*MRIO"):
        sewer_id = mrio_line.sewer_id
        if sewer_id not in lines:
            lines[sewer_id] = []
        lines[sewer_id].append(mrio_line)

    return lines


def get_mrio(lines, putdict, sewerinfo, rmberrors):
    mrios = []

    sewer_id = sewerinfo['sewer_id']

    if not sewer_id or sewer_id.isspace() or sewer_id not in lines:
        return []

    ZYR = None  # Used to store the first ZYR, ZYS and ZYB (reference) we see.
    ZYS = None  # All ZYRs and ZYSs must be the same.
    ZYB = None
    for mrio_line in lines[sewer_id]:
        if mrio_line.ZYR is None:
            rmberrors.append(Error(
                    line_number=mrio_line.line_number,
                    message="Veld ZYR (Type meting) ontbreekt"))
            continue
        if mrio_line.ZYS is None:
            rmberrors.append(Error(
                    line_number=mrio_line.line_number,
                    message="Veld ZYS (Eenheid meetwaarde) ontbreekt"))
            continue
        if mrio_line.ZYB is None:
            rmberrors.append(Error(
                    line_number=mrio_line.line_number,
                    message="Veld ZYB (Referentie) ontbreekt"))
            continue
        if mrio_line.ZYB not in "12":
            rmberrors.append(Error(
                    line_number=mrio_line.line_number,
                    message="Veld ZYB (Referentie) moet waarde 1 of 2 hebben"))
            continue

        if (mrio_line.ZYR.upper() + mrio_line.ZYS.upper() not in
            ("AE", "AF", "CB")):
            rmberrors.append(Error(
                    line_number=mrio_line.line_number,
                    message=("Niet ondersteunde combinatie van type "
                    "meting en eenheid meetwaarde. Alleen A+E, A+F"
                             " en C+B worden ondersteund.")))
            continue

        if ZYR is None:
            ZYR = mrio_line.ZYR
            ZYS = mrio_line.ZYS
            ZYB = mrio_line.ZYB
        else:
            if mrio_line.ZYS != ZYS:
                rmberrors.append(Error(
                        line_number=mrio_line.line_number,
                        message=("ZYS op regel is {line_zys}, terwijl eerder "
                                 "voor deze streng al {zys} gezien is.")
                        .format(line_zys=mrio_line.ZYS, zys=ZYS)))
            if mrio_line.ZYR != ZYR:
                rmberrors.append(Error(
                        line_number=mrio_line.line_number,
                        message=("ZYR op regel is {line_zyr}, terwijl eerder "
                                 "voor deze streng al {zyr} gezien is.")
                        .format(line_zyr=mrio_line.ZYR, zyr=ZYR)))
            if mrio_line.ZYB != ZYB:
                rmberrors.append(Error(
                        line_number=mrio_line.line_number,
                        message=("ZYB op regel is {line_zyb}, terwijl eerder "
                                 "voor deze streng al {zyb} gezien is.")
                        .format(line_zyb=mrio_line.ZYB, zyb=ZYB)))

        mrios.append({
                'sewer_id': sewer_id,
                'distance': mrio_line.distance,
                'reference': mrio_line.ZYB,
                'measurement': mrio_line.measurement,
                'zyrzys': mrio_line.ZYR + mrio_line.ZYS
                })

    if rmberrors or not mrios:
        return []

    mrios.sort(key=lambda mrio: mrio['distance'])

    # Convert to absolute values, set geoms
    # We need the rd_coordinate and bob of both manholes, because they define
    # the so-called "ideal line"
    rd_location_manhole1 = (
        putdict[sewerinfo['manhole_code_1']]['rd_coordinate'])
    rd_location_manhole2 = (
        putdict[sewerinfo['manhole_code_2']]['rd_coordinate'])
    bob1 = sewerinfo['bob_1']
    bob2 = sewerinfo['bob_2']

    if ZYB == "2":
        # Act as if they are the other way around
        rd_location_manhole1, rd_location_manhole2 =\
            rd_location_manhole2, rd_location_manhole1
        bob1, bob2 = bob2, bob1

    set_geoms_dists(
        mrios, rd_location_manhole1, rd_location_manhole2, bob1, bob2,
        zyrzys=(ZYR + ZYS), reverse=(ZYB == "2"))

    return mrios


def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def set_geoms_dists(
    mrios, rd_location_manhole1, rd_location_manhole2,
    bob1, bob2, zyrzys, reverse):
    horizontal_distance = distance(
        rd_location_manhole1, rd_location_manhole2)
    vertical_distance = abs(bob1 - bob2)
    straight_distance = math.sqrt(
        vertical_distance ** 2 + horizontal_distance ** 2)

    dx = rd_location_manhole2[0] - rd_location_manhole1[0]
    dy = rd_location_manhole2[1] - rd_location_manhole1[1]

    prev_bob = bob1
    prev_location = rd_location_manhole1

    for mrio in mrios:
        percentage_along = mrio['distance'] / straight_distance

        mrio['rd_coordinate'] = (
            rd_location_manhole1[0] + percentage_along * dx,
            rd_location_manhole1[1] + percentage_along * dy)
        mrio['coordinate'] = util.rd_to_wgs84(*mrio['rd_coordinate'])

        mrio['dist'] = percentage_along * horizontal_distance

        if zyrzys == "AE":
            # Slope in degrees
            mrio['bob'] = prev_bob + (
                distance(prev_location, mrio['rd_coordinate']) *
                math.tan(mrio['measurement'] / 180 * math.pi))
        elif zyrzys == "AF":
            # Slope in percent
            mrio['bob'] = prev_bob + (
                distance(prev_location, mrio['rd_coordinate']) *
                mrio['measurement'] / 100.0)
        elif zyrzys == "CB":
            # Meters relative to the ideal line
            mrio['bob'] = (bob1 + (bob2 - bob1) * percentage_along +
                           mrio['measurement'])

        prev_bob = mrio['bob']
        prev_location = mrio['rd_coordinate']

    if reverse:
        for mrio in mrios:
            mrio['dist'] = horizontal_distance - mrio['dist']


def save_into_database(rib_path, rmb_path, putdict, sewerdict, rmberrors):
    # Get sewerage name, try to create sewerage
    # If it exists, return with an error
    sewerage_name = os.path.basename(rmb_path)[:-4]  # Minus ".RMB"

    if models.Sewerage.objects.filter(name=sewerage_name).exists():
        rmberrors.append(Error(
                line_number=0,
                message=("Er bestaat al een stelsel met de naam {name}. "
                 "Verwijder het op de archiefpagina, of gebruik "
                 "een andere naam.").format(name=sewerage_name)))
        return

    # Files are copied only at the end
    sewerage = models.Sewerage.objects.create(
        name=sewerage_name,
        rib=None,  # Filled in later
        rmb=None,
        active=True)

    # Save the puts, keep a dictionary
    saved_puts = dict()
    for put_id, putinfo in putdict.items():
        saved_puts[put_id] = models.Manhole.objects.create(
            sewerage=sewerage,
            code=put_id,
            sink=int(putinfo['is_sink']),
            ground_level=putinfo['surface_level'],
            the_geom=Point(*putinfo['coordinate']))

    # Save the sewers, use the dictionary
    saved_sewers = dict()
    for sewer_id, sewerinfo in sewerdict.items():
        manhole1 = saved_puts[sewerinfo['manhole_code_1']]
        manhole2 = saved_puts[sewerinfo['manhole_code_2']]
        saved_sewers[sewer_id] = models.Sewer.objects.create(
            sewerage=sewerage,
            code=sewer_id,
            quality=models.Sewer.QUALITY_UNKNOWN,
            diameter=sewerinfo['diameter'],
            manhole1=manhole1,
            manhole2=manhole2,
            bob1=sewerinfo['bob_1'],
            bob2=sewerinfo['bob_2'],
            the_geom=LineString(manhole1.the_geom, manhole2.the_geom))

    # Save the measurements
    sewer_measurements = []
    for sewer_id, sewerinfo in sewerdict.items():
        measurements = sewerinfo['measurements']

        for m in measurements:
            sewer_measurements.append(
                models.SewerMeasurement(
                    sewer=saved_sewers[sewer_id],
                    distance=m['dist'],
                    virtual=False,
                    water_level=None,
                    flooded_pct=None,
                    bob=m['bob'],
                    obb=m['bob'] + sewerinfo['diameter'],
                    the_geom=Point(*m['coordinate'])))

    models.SewerMeasurement.objects.bulk_create(sewer_measurements)
