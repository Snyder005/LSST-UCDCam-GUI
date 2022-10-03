#!/usr/bin/python

# LSST FITS Header Conformance Tools
# Opens a file (or set of files) written by UCDavis
# Optical Simulator and modifes the 
# header to conform to LSST EO Test data standards
# Craig Lage 8-Jan-15 copied from Peter Doherty at Harvard
# and modified.

import pyfits as pf
import numpy as np
import sys
import os
import glob
import eolib
import hdrtools
import warnings


###########################################################################
###########################################################################
# This ignores an annoying deprecation warning.  Will fix later.
warnings.simplefilter("ignore")

def fix(infile, config_file, sensor_id, masktype, testtype, imagetype, seqnum, exptime, filter, srcpwr, mondiode, temp_a, temp_b, temp_set, stage_pos=[0.0,0.0,0.0]):

    verbose = True   # set to True to make this thing verbose
    
    # Announce yourself, if being verbose
    if ( verbose == True ) : print 'LSST FITS Header Conformance Tool',' v0.1'

    if not os.path.isfile(infile):
        print "Specified FITS file does not exist. Returning."
        return
    if not os.path.isfile(config_file):
        print "Specified configuration file does not exist. Returning."
        return
   
    # Badval is used to mark values we do not have valid information for
    badval = -999999.99

    # get information from configuration file
    origin   = str.upper(eolib.getCfgVal(config_file, 'LSST_LAB'))
    tstand   = str.upper(eolib.getCfgVal(config_file, 'TSTAND'))
    controll = str.upper(eolib.getCfgVal(config_file, 'CONTROLL'))
    contnum  = str.upper(eolib.getCfgVal(config_file, 'CONTNUM'))
    instrume = str.upper(eolib.getCfgVal(config_file, 'INSTRUME'))
    lamptype = str.upper(eolib.getCfgVal(config_file, 'LAMPTYPE'))
    srcmodl  = str.upper(eolib.getCfgVal(config_file, 'SRCMODL'))
    monotype = str.upper(eolib.getCfgVal(config_file, 'MONOTYPE'))
    monomodl = str.upper(eolib.getCfgVal(config_file, 'MONOMODL'))
    pd_model = str.upper(eolib.getCfgVal(config_file, 'PD_MODEL'))
    pd_ser   = str.upper(eolib.getCfgVal(config_file, 'PD_SER'))
    ccd_manu = str.upper(eolib.getCfgVal(config_file, 'CCD_MANU'))
    ccd_type = str.upper(eolib.getCfgVal(config_file, 'CCD_TYPE'))
    ccd_sern = str.upper(eolib.getCfgVal(config_file, 'CCD_SERN'))
    ccd_gain = str.upper(eolib.getCfgVal(config_file, 'SYS_GAIN'))
    mask_sern = str.upper(eolib.getCfgVal(config_file, 'MASK_SERN'))
    shut_del = str.upper(eolib.getCfgVal(config_file, 'SHUT_DEL'))

    print 'Processing FITS file :', infile

    # open the file
    # do_not_scale_image_data=True is important so as not to mess up the data format.
    # checksum=True is required to calculate the checksums and datasums
    hdulist = pf.open(infile, mode='update', checksum=True, do_not_scale_image_data=True)

    ### fix the primary header first
    phdr=hdulist[0].header
    phdr.add_history("Updated via LSST FITS Header Conformance Tool")
    phdr_keys = phdr.keys()
    
    ###########################################################################
    # add or update some basic keywords as required
    phdr.update('ORIGIN', origin, 'CCD Test Laboratory', after='EXTEND')
    phdr.update('DATE', phdr['DATE'], 'Creation date', after='ORIGIN')
    phdr.update('DATE-OBS', phdr['DATE'], 'Observation date', after='DATE')

    (JD, MJD) = date_to_jd(phdr['DATE'])
    phdr.update('MJD', MJD, 'Modified Julian Date of data acquisition', after='DATE-OBS')
    phdr.update('JD', JD, 'Julian Date of data acquisition', after='MJD')

    phdr.update('IMAGETAG', 'NONE', ' ', after='JD') 
    phdr.update('TSTAND',   tstand, 'CCD Test Stand', after='IMAGETAG')
    phdr.update('INSTRUME', instrume, 'Instrument', after='TSTAND')
    phdr.update('CONTROLL', controll, 'CCD Controller', after='INSTRUME')
    phdr.update('CONTNUM',  contnum, 'CCD Controller', after='CONTROLL')
    phdr.update('CCD_MANU', ccd_manu, 'CCD manufacturer', after='CONTNUM')
    phdr.update('CCD_TYPE', ccd_type, 'CCD type', after='CCD_MANU')
    phdr.update('CCD_SERN', ccd_sern, 'CCD serial number', after='CCD_TYPE')   
    phdr.update('LSST_NUM', sensor_id, 'LSST CCD number', after='CCD_SERN')   
    phdr.update('TESTTYPE', testtype, 'Test type', after='LSST_NUM') 
    phdr.update('IMGTYPE', imagetype, 'Image type', after='TESTTYPE')
    phdr.update('SEQNUM', seqnum, 'Image number in sequence', after='IMGTYPE')
    
    ###########################################################################
    # delete some meaningless comment keys
    hdrtools.delKey(phdr, 'COMMENT')
    hdrtools.delKey(phdr, 'COMMENT')

    ###########################################################################
    # fix temperature and setpoint  
    phdr.update('TEMP_SET', temp_set, 'CCD temperature setpoint', after='SEQNUM')
    phdr.update('CCDTEMP', temp_b, 'Measured CCD temperature', after = 'TEMP_SET')

    ###########################################################################
    # fix monitor diode value 
    phdr.update('MONDIODE', mondiode, '[pA] Monitor diode current', after='CCDTEMP')
    
    ###########################################################################
    # fix monochromator wavelength 
    if 'MONOWL' in phdr_keys : 
        phdr.update('MONOWL', phdr['MONOWL'], 'Monochromator wavelength', after='MONDIODE')
        monowl = phdr['MONOWL']
    else :
        if 'MONO_WAVELENG' in phdr_keys : 
            phdr.update('MONOWL', phdr['MONO_WAVELENG'], 'Monochromator wavelength', after='MONDIODE')
            monowl = phdr['MONO_WAVELENG']
        else :
            phdr.update('MONOWL', badval, 'Monochromator wavelength', after='MONDIODE')
            monowl = 'UNKNOWN'
            
    ###########################################################################
    # fix filter setting 
            
    phdr.update('FILTER', filter, 'Optical filter', after='MONOWL')
    phdr.update('MASK_TYP', masktype, 'Mask Type', after='FILTER')
    phdr.update('MASK_SER', mask_sern, 'Mask Serial Number', after='MASK_TYP')
    
    phdr.update('EXPTIME', exptime, '[s] Exposure time', after='MASK_SER')
    phdr.update('SHUT_DEL', shut_del, '[ms] Shutter Delay', after='EXPTIME')
    phdr.update('CTLRCFG', config_file, 'Controller config file', after='SHUT_DEL')
    phdr.update('FILENAME', infile, 'Original file name', after='CTLRCFG')
    phdr.update('DETSIZE', '[1:4336,1:4044]', 'NOAO detector size', after='FILENAME')
    phdr.update('BINNING', 1, '[pixelX x pixelY] chip binning', after='DETSIZE')
    phdr.update('BINX', 1, '[pixels] binning along X axis', after='BINNING')
    phdr.update('BINY', 1, '[pixels] binning along Y axis', after='BINX')

    ###########################################################################

    # fix geometry keywords
    #
    if phdr['CCD_MANU'] == 'ITL' :
        phdr.update('PRE_COLS', 3, 'Prescan columns', after='BINY')
        phdr.update('IMG_COLS', 509, 'Imaging columns', after='PRE_COLS')
        phdr.update('OVR_COLS', 30, 'Overscan columns', after='IMG_COLS')
        phdr.update('PRE_ROWS', 0, 'Prescan rows', after='OVR_COLS')
        phdr.update('IMG_ROWS', 2000, 'Imaging rows', after='PRE_ROWS')
        phdr.update('OVR_ROWS', 22, 'Overscan rows ', after='IMG_ROWS')
    else :
        if phdr['CCD_MANU'] == 'E2V' :
            phdr.update('PRE_COLS', 10, 'Prescan columns', after='BINY')
            phdr.update('IMG_COLS', 512, 'Imaging columns', after='PRE_COLS')
            phdr.update('OVR_COLS', 20, 'Overscan columns', after='IMG_COLS')
            phdr.update('PRE_ROWS', 0, 'Prescan rows', after='OVR_COLS')
            phdr.update('IMG_ROWS', 2002, 'Imaging rows', after='PRE_ROWS')
            phdr.update('OVR_ROWS', 20, 'Overscan rows ', after='IMG_ROWS')
        else :
            print "Not ITL or E2V"
            phdr.update('PRE_COLS', 4, 'Prescan columns', after='BINY')
            phdr.update('IMG_COLS', 509, 'Imaging columns', after='PRE_COLS')
            phdr.update('OVR_COLS', 20, 'Overscan columns', after='IMG_COLS')
            phdr.update('PRE_ROWS', 0, 'Prescan rows', after='OVR_COLS')
            phdr.update('IMG_ROWS', 2000, 'Imaging rows', after='PRE_ROWS')
            phdr.update('OVR_ROWS', 20, 'Overscan rows ', after='IMG_ROWS')

    phdr.update('HEADVER', 1, 'LSST FITS header version', after='OVR_ROWS')
    phdr.update('CCDGAIN', ccd_gain, '[e/DN] estimated CCD gain', after='HEADVER')
    phdr.update('CCDNOISE', 'UNKNOWN', '[e- rms] estimated CCD noise', after='CCDGAIN')
    phdr.update('CHECKSUM', 0, 'file checksum', after='CCDNOISE')
    phdr.update('DATASUM', 0, 'data checksum', after='CHECKSUM')

    ###########################################################################
    # fix up the various image extensions
    
    for i in range(1,17) :
        imhdr=hdulist[i].header

        if   i == 8 :  
            extname = 'SEGMENT10'
            imhdr.update('DETSEC', '[509:1,1:2000]')
        elif i == 7 :  
            extname = 'SEGMENT11'
            imhdr.update('DETSEC', '[1018:510,1:2000]')
        elif i == 6 :  
            extname = 'SEGMENT12'
            imhdr.update('DETSEC', '[1527:1019,1:2000]')
        elif i == 5 :  
            extname = 'SEGMENT13'
            imhdr.update('DETSEC', '[2036:1528,1:2000]')
        elif i == 4 :  
            extname = 'SEGMENT14'
            imhdr.update('DETSEC', '[2545:2037,1:2000]')
        elif i == 3 :  
            extname = 'SEGMENT15'
            imhdr.update('DETSEC', '[3054:2546,1:2000]')
        elif i == 2 :  
            extname = 'SEGMENT16'
            imhdr.update('DETSEC', '[3563:3055,1:2000]')            
        elif i == 1 :  
            extname = 'SEGMENT17'
            imhdr.update('DETSEC', '[4072:3564,1:2000]')
        elif i == 9 :  
            extname = 'SEGMENT07'
            imhdr.update('DETSEC', '[4072:3564,4000:2001]')
        elif i == 10 : 
            extname = 'SEGMENT06'
            imhdr.update('DETSEC', '[3563:3055,4000:2001]')
        elif i == 11 : 
            extname = 'SEGMENT05'
            imhdr.update('DETSEC', '[3054:2546,4000:2001]')
        elif i == 12 : 
            extname = 'SEGMENT04'
            imhdr.update('DETSEC', '[2545:2037,4000:2001]')
        elif i == 13 : 
            extname = 'SEGMENT03'
            imhdr.update('DETSEC', '[2036:1528,4000:2001]')
        elif i == 14 : 
            extname = 'SEGMENT02'
            imhdr.update('DETSEC', '[1527:1019,4000:2001]')
        elif i == 15 : 
            extname = 'SEGMENT01'
            imhdr.update('DETSEC', '[1018:510,4000:2001]')
        elif i == 16 : 
            extname = 'SEGMENT00'
            imhdr.update('DETSEC', '[509:1,4000:2001]')
        else: print "Whoops! That's not a valid extension! "

        imhdr.update('DETSIZE', '[1:4072,1:4000]')
        imhdr.update('DATASEC', '[4:512,1:2000]')
        imhdr.update('CHANNEL', i, 'channel number', after='BSCALE')    
        imhdr.update('EXTNAME', extname, 'LSST segment identifier', after='CHANNEL')

        data = np.array(hdulist[i].data + 32768, dtype = np.int16)
        # Data is stored as unsigned 16 bit integers, so we need to apply this transformation
        # in order to calculate the mean and std deviation.

        imhdr.update('AVERAGE', data.mean(), 'Data Mean', after='EXTNAME')
        imhdr.update('STDEV', data.std(), 'Data Std Dev', after='AVERAGE')

        imhdr.update('DTV2', 0.0, after='DTV1')
        imhdr.update('DTM1_2', 0.0, after='DTM1_1')
        imhdr.update('DTM2_1', 0.0, after='DTM1_2')
        imhdr.update('LTM1_2', 0.0, after='LTM1_1')
        imhdr.update('LTM2_1', 0.0, after='LTM1_2')
        imhdr.update('ATM1_2', 0.0, after='ATM1_1')
        imhdr.update('ATM2_1', 0.0, after='ATM1_2')

        # Calculate LTM and LTV values
	row = int(extname[7:8])  # first number of extname
	col = int(extname[8:9])  # second number of extname
        pre = phdr['PRE_COLS']  # number of pre-columns in segment image
	xsize = phdr['IMG_COLS']  # number columns in segment image
	ysize = phdr['IMG_ROWS']  # number rows in segment image        

        imhdr.update('LTM1_1', -1.0, after='ATV2')
        imhdr.update('LTM2_2', -1.0 + 2.0*row, after='LTM1_1')
        imhdr.update('LTV1', (col + 1)*xsize + 1 + pre, after='DTV2')
        imhdr.update('LTV2', (2*ysize +1)*(1 - row), after='LTV1')

        imhdr.update('DETECTOR', ccd_sern)
        imhdr.update('CHECKSUM', 0, 'file checksum', after='ATM2_2')
        imhdr.update('DATASUM', 0, 'data checksum', after='CHECKSUM')
        # delete meaningless CTYPE keys
        hdrtools.delKey(imhdr, 'CTYPE1')
        hdrtools.delKey(imhdr, 'CTYPE2')

    ###########################################################################
    # create and fill the Test Condition extension 

    dat=np.array([])
    tchdu = pf.ImageHDU( data=dat, header=None, name='TEST_COND')
    tchdr = tchdu.header

    tchdr.update('XTENSION', 'BINTABLE', 'N.B. Does not contain any data')
    tchdr.update('BITPIX', 8, after='XTENSION')
    tchdr.update('NAXIS', 2, after='BITPIX')
    tchdr.update('NAXIS1', 0, 'Width of table in bytes', after='NAXIS')
    tchdr.update('NAXIS2', 0, 'Number of rows in table', after='NAXIS1')
    tchdr.update('PCOUNT', 0, 'Size of special data area', after='NAXIS2')
    tchdr.update('GCOUNT', 1, 'One data group', after='PCOUNT')

    tchdr.update('EXTNAME', 'TEST_COND', 'Name of extension', after='GCOUNT')
    # add the newly created Test Conditions HDU to the file
    hdulist.insert(17, tchdu)
    tchdr = hdulist[17].header

    tchdr.update('TEMP_SET', temp_set, 'Temperature set point', after='EXTNAME')
    tchdr.update('CCDTEMP', temp_b, 'Measured CCD temperature', after='TEMP_SET')


    tchdr.update('ROOMTEMP', badval, 'Room Temperature', after='CCDTEMP')
    tchdr.update('DWRTEMP',  temp_a, 'External dewar temperature', after='ROOMTEMP')
    tchdr.update('DWRPRESS', badval, '[Torr] Dewar internal pressure level', after='DWRTEMP')
    tchdr.update('SRCTYPE', lamptype, 'Lamp type', after='DWRPRESS')
    tchdr.update('SRCMODL', srcmodl, 'Lamp model number',after='SRCTYPE')  
    tchdr.update('SRCPWR', srcpwr, 'Light source power (%)', after='SRCMODL')  

    tchdr.update('ND_FILT', phdr['FILTER'], 'ND filter after lamp, if any', after='SRCPWR')
    tchdr.update('FILTER', phdr['FILTER'], 'Optical filter used', after='ND_FILT')
    tchdr.update('MONOTYPE', monotype, 'Monochromator manufacturer', after='FILTER')
    tchdr.update('MONOMODL', monomodl, 'Monochromator model number', after='MONOTYPE') 
    
    tchdr.update('MONOPOS', 1, 'Monochromator grating turrent position', after='MONOMODL')
    tchdr.update('MONOGRAT', 1200, 'Monochromator grating in use', after='MONOPOS')
    tchdr.update('MONOWL', monowl, 'Monochromator wavelength', after='MONOGRAT')
    tchdr.update('PD_MODEL', pd_model, 'Monitor photodiode model', after='MONOWL')
    tchdr.update('PD_SER', pd_ser, 'Monitor photodiode serial number', after='PD_MODEL')
    tchdr.update('X_POS', stage_pos[0], 'Stage relative X-position from encoder', after='PD_SER')
    tchdr.update('Y_POS', stage_pos[1], 'Stage relative Y-position from encoder', after='X_POS')
    tchdr.update('Z_POS', stage_pos[2], 'Stage relative Z-position from encoder', after='Y_POS')
    tchdr.update('CHECKSUM', 0, after='Z_POS')
    tchdr.update('DATASUM', 0, after='CHECKSUM')   


    ###########################################################################
    # create and fill the CCD Condition extension

    dat=np.array([])
    cchdu = pf.ImageHDU(data=dat, header=None, name='CCD_COND')
    cchdr = cchdu.header
    cchdr.update('XTENSION', 'BINTABLE', 'N.B. Does not contain any data')
    cchdr.update('BITPIX', 8, after='XTENSION')
    cchdr.update('NAXIS', 2, after='BITPIX')
    cchdr.update('NAXIS1', 0, 'Width of table in bytes', after='NAXIS')
    cchdr.update('NAXIS2', 0, 'Number of rows in table', after='NAXIS1')
    cchdr.update('PCOUNT', 0, 'Size of special data area', after='NAXIS2')
    cchdr.update('GCOUNT', 1, 'One data group', after='PCOUNT')

    cchdr.update('EXTNAME', 'CCD_COND', 'Name of extension', after='GCOUNT')
    cchdr.update('CHECKSUM', 0, after='EXTNAME')
    cchdr.update('DATASUM', 0, after='CHECKSUM')   


    hdulist.insert(18,cchdu)
    cchdr=hdulist[18].header
    
    cchdr.update('V_S1L', eolib.getCfgVal(config_file,'SER_CLK_LO'), 'Serial clock lower rail voltage')
    cchdr.update('V_S1H', eolib.getCfgVal(config_file,'SER_CLK_HI'), 'Serial clock upper rail voltage')
    cchdr.update('V_S2L', eolib.getCfgVal(config_file,'SER_CLK_LO'), 'Serial clock lower rail voltage')
    cchdr.update('V_S2H', eolib.getCfgVal(config_file,'SER_CLK_HI'), 'Serial clock upper rail voltage')
    cchdr.update('V_S3L', eolib.getCfgVal(config_file,'SER_CLK_LO'), 'Serial clock lower rail voltage')
    cchdr.update('V_S3H', eolib.getCfgVal(config_file,'SER_CLK_HI'), 'Serial clock upper rail voltage')

    cchdr.update('V_RGL', eolib.getCfgVal(config_file,'RG_LO'), 'Reset Gate clock lower rail voltage')
    cchdr.update('V_RGH', eolib.getCfgVal(config_file,'RG_HI'), 'Reset Gate clock upper rail voltage')

    cchdr.update('V_P1L', eolib.getCfgVal(config_file,'PAR_CLK_LO'), 'Parallel clock lower rail voltage')
    cchdr.update('V_P1H', eolib.getCfgVal(config_file,'PAR_CLK_HI'), 'Parallel clock upper rail voltage')
    cchdr.update('V_P2L', eolib.getCfgVal(config_file,'PAR_CLK_LO'), 'Parallel clock lower rail voltage')
    cchdr.update('V_P2H', eolib.getCfgVal(config_file,'PAR_CLK_HI'), 'Parallel clock upper rail voltage')
    cchdr.update('V_P3L', eolib.getCfgVal(config_file,'PAR_CLK_LO'), 'Parallel clock lower rail voltage')
    cchdr.update('V_P3H', eolib.getCfgVal(config_file,'PAR_CLK_HI'), 'Parallel clock upper rail voltage')
    cchdr.update('V_P4L', eolib.getCfgVal(config_file,'PAR_CLK_LO'), 'Parallel clock lower rail voltage')
    cchdr.update('V_P4H', eolib.getCfgVal(config_file,'PAR_CLK_HI'), 'Parallel clock upper rail voltage')

    cchdr.update('V_GD', eolib.getCfgVal(config_file,'LSS'), 'Front side ground voltage')
    cchdr.update('V_BSS', eolib.getCfgVal(config_file,'BSS_TEST'), 'Backside Substrate voltage')
    cchdr.update('VDD', eolib.getCfgVal(config_file,'VDD'), 'Dump Drain voltage')
    
    # Update VOD voltages. We only have one, but we write 16 times
    ODval = eolib.getCfgVal(config_file,'VOD')
        
    cchdr.update('V_OD1',  ODval, 'Amplifier 1 output drain voltage')
    cchdr.update('V_OD2',  ODval, 'Amplifier 2 output drain voltage')
    cchdr.update('V_OD3',  ODval, 'Amplifier 3 output drain voltage')
    cchdr.update('V_OD4',  ODval, 'Amplifier 4 output drain voltage')
    cchdr.update('V_OD5',  ODval, 'Amplifier 5 output drain voltage')
    cchdr.update('V_OD6',  ODval, 'Amplifier 6 output drain voltage')
    cchdr.update('V_OD7',  ODval, 'Amplifier 7 output drain voltage')
    cchdr.update('V_OD8',  ODval, 'Amplifier 8 output drain voltage')
    cchdr.update('V_OD9',  ODval, 'Amplifier 9 output drain voltage')
    cchdr.update('V_OD10', ODval, 'Amplifier 10 output drain voltage')
    cchdr.update('V_OD11', ODval, 'Amplifier 11 output drain voltage')
    cchdr.update('V_OD12', ODval, 'Amplifier 12 output drain voltage')
    cchdr.update('V_OD13', ODval, 'Amplifier 13 output drain voltage')
    cchdr.update('V_OD14', ODval, 'Amplifier 14 output drain voltage')
    cchdr.update('V_OD15', ODval, 'Amplifier 15 output drain voltage')
    cchdr.update('V_OD16', ODval, 'Amplifier 16 output drain voltage')

    # Update VRD voltages. We only have one, but we write 16 times
    RDval = eolib.getCfgVal(config_file,'VRD')
        
    cchdr.update('V_RD1',  RDval, 'Amplifier 1 reset drain voltage')
    cchdr.update('V_RD2',  RDval, 'Amplifier 2 reset drain voltage')
    cchdr.update('V_RD3',  RDval, 'Amplifier 3 reset drain voltage')
    cchdr.update('V_RD4',  RDval, 'Amplifier 4 reset drain voltage')
    cchdr.update('V_RD5',  RDval, 'Amplifier 5 reset drain voltage')
    cchdr.update('V_RD6',  RDval, 'Amplifier 6 reset drain voltage')
    cchdr.update('V_RD7',  RDval, 'Amplifier 7 reset drain voltage')
    cchdr.update('V_RD8',  RDval, 'Amplifier 8 reset drain voltage')
    cchdr.update('V_RD9',  RDval, 'Amplifier 9 reset drain voltage')
    cchdr.update('V_RD10', RDval, 'Amplifier 10 reset drain voltage')
    cchdr.update('V_RD11', RDval, 'Amplifier 11 reset drain voltage')
    cchdr.update('V_RD12', RDval, 'Amplifier 12 reset drain voltage')
    cchdr.update('V_RD13', RDval, 'Amplifier 13 reset drain voltage')
    cchdr.update('V_RD14', RDval, 'Amplifier 14 reset drain voltage')
    cchdr.update('V_RD15', RDval, 'Amplifier 15 reset drain voltage')
    cchdr.update('V_RD16', RDval, 'Amplifier 16 reset drain voltage')

    # Update VOG voltages. We only have one, but we write 16 times
    OGval = eolib.getCfgVal(config_file,'VOG')
        
    cchdr.update('V_OG1',  OGval, 'Amplifier 1 output gate voltage')
    cchdr.update('V_OG2',  OGval, 'Amplifier 2 output gate voltage')
    cchdr.update('V_OG3',  OGval, 'Amplifier 3 output gate voltage')
    cchdr.update('V_OG4',  OGval, 'Amplifier 4 output gate voltage')
    cchdr.update('V_OG5',  OGval, 'Amplifier 5 output gate voltage')
    cchdr.update('V_OG6',  OGval, 'Amplifier 6 output gate voltage')
    cchdr.update('V_OG7',  OGval, 'Amplifier 7 output gate voltage')
    cchdr.update('V_OG8',  OGval, 'Amplifier 8 output gate voltage')
    cchdr.update('V_OG9',  OGval, 'Amplifier 9 output gate voltage')
    cchdr.update('V_OG10', OGval, 'Amplifier 10 output gate voltage')
    cchdr.update('V_OG11', OGval, 'Amplifier 11 output gate voltage')
    cchdr.update('V_OG12', OGval, 'Amplifier 12 output gate voltage')
    cchdr.update('V_OG13', OGval, 'Amplifier 13 output gate voltage')
    cchdr.update('V_OG14', OGval, 'Amplifier 14 output gate voltage')
    cchdr.update('V_OG15', OGval, 'Amplifier 15 output gate voltage')
    cchdr.update('V_OG16', OGval, 'Amplifier 16 output gate voltage')

    # the SAO controller can't measure these, so we set them to 'badval'

    cchdr.update('I_OD1',  badval, 'Amplifier 1 output drain current in uA')
    cchdr.update('I_OD2',  badval, 'Amplifier 2 output drain current in uA')
    cchdr.update('I_OD3',  badval, 'Amplifier 3 output drain current in uA')
    cchdr.update('I_OD4',  badval, 'Amplifier 4 output drain current in uA')
    cchdr.update('I_OD5',  badval, 'Amplifier 5 output drain current in uA')
    cchdr.update('I_OD6',  badval, 'Amplifier 6 output drain current in uA')
    cchdr.update('I_OD7',  badval, 'Amplifier 7 output drain current in uA')
    cchdr.update('I_OD8',  badval, 'Amplifier 8 output drain current in uA')
    cchdr.update('I_OD9',  badval, 'Amplifier 9 output drain current in uA')
    cchdr.update('I_OD10', badval, 'Amplifier 10 output drain current in uA')
    cchdr.update('I_OD11', badval, 'Amplifier 11 output drain current in uA')
    cchdr.update('I_OD12', badval, 'Amplifier 12 output drain current in uA')
    cchdr.update('I_OD13', badval, 'Amplifier 13 output drain current in uA')
    cchdr.update('I_OD14', badval, 'Amplifier 14 output drain current in uA')
    cchdr.update('I_OD15', badval, 'Amplifier 15 output drain current in uA')
    cchdr.update('I_OD16', badval, 'Amplifier 16 output drain current in uA')

    cchdr.update('I_RD1',  badval, 'Amplifier 1 reset drain current in uA')
    cchdr.update('I_RD2',  badval, 'Amplifier 2 reset drain current in uA')
    cchdr.update('I_RD3',  badval, 'Amplifier 3 reset drain current in uA')
    cchdr.update('I_RD4',  badval, 'Amplifier 4 reset drain current in uA')
    cchdr.update('I_RD5',  badval, 'Amplifier 5 reset drain current in uA')
    cchdr.update('I_RD6',  badval, 'Amplifier 6 reset drain current in uA')
    cchdr.update('I_RD7',  badval, 'Amplifier 7 reset drain current in uA')
    cchdr.update('I_RD8',  badval, 'Amplifier 8 reset drain current in uA')
    cchdr.update('I_RD9',  badval, 'Amplifier 9 reset drain current in uA')
    cchdr.update('I_RD10', badval, 'Amplifier 10 reset drain current in uA')
    cchdr.update('I_RD11', badval, 'Amplifier 11 reset drain current in uA')
    cchdr.update('I_RD12', badval, 'Amplifier 12 reset drain current in uA')
    cchdr.update('I_RD13', badval, 'Amplifier 13 reset drain current in uA')
    cchdr.update('I_RD14', badval, 'Amplifier 14 reset drain current in uA')
    cchdr.update('I_RD15', badval, 'Amplifier 15 reset drain current in uA')
    cchdr.update('I_RD16', badval, 'Amplifier 16 reset drain current in uA')

    cchdr.update('I_OG1',  badval, 'Amplifier 1 output gate current in uA')
    cchdr.update('I_OG2',  badval, 'Amplifier 2 output gate current in uA')
    cchdr.update('I_OG3',  badval, 'Amplifier 3 output gate current in uA')
    cchdr.update('I_OG4',  badval, 'Amplifier 4 output gate current in uA')
    cchdr.update('I_OG5',  badval, 'Amplifier 5 output gate current in uA')
    cchdr.update('I_OG6',  badval, 'Amplifier 6 output gate current in uA')
    cchdr.update('I_OG7',  badval, 'Amplifier 7 output gate current in uA')
    cchdr.update('I_OG8',  badval, 'Amplifier 8 output gate current in uA')
    cchdr.update('I_OG9',  badval, 'Amplifier 9 output gate current in uA')
    cchdr.update('I_OG10', badval, 'Amplifier 10 output gate current in uA')
    cchdr.update('I_OG11', badval, 'Amplifier 11 output gate current in uA')
    cchdr.update('I_OG12', badval, 'Amplifier 12 output gate current in uA')
    cchdr.update('I_OG13', badval, 'Amplifier 13 output gate current in uA')
    cchdr.update('I_OG14', badval, 'Amplifier 14 output gate current in uA')
    cchdr.update('I_OG15', badval, 'Amplifier 15 output gate current in uA')
    cchdr.update('I_OG16', badval, 'Amplifier 16 output gate current in uA')

    cchdr.update('I_GD', badval, 'Ground current in uA')
    cchdr.update('I_BSS', badval, 'BSS current in uA')    

    # add the newly created CCD Conditions HDU to the file

    # finished. Close file.
    #hdulist.close(output_verify='ignore')
    hdulist.close()

    print 'FITS file conversion done.'

    return


def date_to_jd(date):
    """
    Convert a date to Julian Day.
    
    Algorithm from 'Practical Astronomy with your Calculator or Spreadsheet', 
        4th ed., Duffet-Smith and Zwart, 2011.
    Assumes the date is after the start of the Gregorian calendar.
    """
    year = int(date.split()[5])
    alpha_month = date.split()[1]
    day = int(date.split()[2])
    if alpha_month == "Jan":
        month = 1
    elif alpha_month == "Feb":
        month = 2
    elif alpha_month == "Mar":
        month = 3
    elif alpha_month == "Apr":
        month = 4
    elif alpha_month == "May":
        month = 5
    elif alpha_month == "Jun":
        month = 6
    elif alpha_month == "Jul":
        month = 7
    elif alpha_month == "Aug":
        month = 8
    elif alpha_month == "Sep":
        month = 9
    elif alpha_month == "Oct":
        month = 10
    elif alpha_month == "Nov":
        month = 11
    elif alpha_month == "Dec":
        month = 12

    if month == 1 or month == 2:
        yearp = year - 1
        monthp = month + 12
    else:
        yearp = year
        monthp = month

    # after start of Gregorian calendar
    A = np.trunc(yearp / 100.)
    B = 2 - A + np.trunc(A / 4.)

    C = np.trunc(365.25 * yearp)
        
    D = np.trunc(30.6001 * (monthp + 1))
    
    jd = B + C + D + day + 1720994.5

    hour = int(date.split()[3].split(':')[0])
    minute = int(date.split()[3].split(':')[1])
    second = int(date.split()[3].split(':')[2])

    jd = jd + (hour + minute / 60.0 + second / 3600.0) / 24.0
    mjd = jd - 2400000.5
    
    return ("%.5f"%jd, "%.5f"%mjd)







