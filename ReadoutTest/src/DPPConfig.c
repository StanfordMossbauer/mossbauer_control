/* Mostly taken from:
 * https://github.com/cjpl/caen-suite/blob/master/WaveDump/src/WDconfig.c
 *
 * Trying to adapt demo-c code to take a config file so we don't have to keep rebuilding.
 * (Joey 2022/09/20)
 */


#include <CAENDigitizerType.h>
#include "config.h"


/*! \fn      void SetDefaultConfiguration(DPPConfig_t *DPPcfg) 
*   \brief   Fill the Configuration Structure with Default Values
*            
*   \param   DPPcfg:   Pointer to the DPPConfig data structure
*/
static void SetDefaultConfiguration(DPPConfig_t *DPPcfg) {
    int i, j;

    DPPcfg->RecordLength = (1024*16);
	DPPcfg->PostTrigger = 80;
	DPPcfg->NumEvents = 1023;
	DPPcfg->EnableMask = 0xFFFF;
	DPPcfg->GWn = 0;
    DPPcfg->ExtTriggerMode = CAEN_DGTZ_TRGMODE_ACQ_ONLY;
    DPPcfg->InterruptNumEvents = 0;
    DPPcfg->TestPattern = 0;
	DPPcfg->DecimationFactor = 1;
    DPPcfg->TriggerEdge = 0;
    DPPcfg->DesMode = 0;
	DPPcfg->FastTriggerMode = 0; 
    DPPcfg->FastTriggerEnabled = 0; 
	DPPcfg->FPIOtype = 0;
	strcpy(DPPcfg->GnuPlotPath, GNUPLOT_DEFAULT_PATH);
	for(i=0; i<MAX_SET; i++) {
		DPPcfg->DCoffset[i] = 0;
		DPPcfg->Threshold[i] = 0;
        DPPcfg->ChannelTriggerMode[i] = CAEN_DGTZ_TRGMODE_DISABLED;
		DPPcfg->GroupTrgEnableMask[i] = 0;
		for(j=0; j<MAX_SET; j++) DPPcfg->DCoffsetGrpCh[i][j] = -1;
		DPPcfg->FTThreshold[i] = 0;
		DPPcfg->FTDCoffset[i] =0;
    }
    DPPcfg->useCorrections = -1;
    DPPcfg->UseManualTables = -1;
    for(i=0; i<MAX_X742_GROUP_SIZE; i++)
        sprintf(DPPcfg->TablesFilenames[i], "Tables_gr%d", i);
    DPPcfg->DRS4Frequency = CAEN_DGTZ_DRS4_5GHz;
}



/*! \fn      int ParseConfigFile(FILE *f_ini, DPPConfig_t *DPPcfg) 
*   \brief   Read the configuration file and set the DPP paremeters
*            
*   \param   f_ini        Pointer to the config file
*   \param   DPPcfg:   Pointer to the DPPConfig data structure
*   \return  0 = Success; negative numbers are error codes; positive numbers
*               decodes the changes which need to perform internal parameters
*               recalculations.
*/
int ParseConfigFile(FILE *f_ini, DPPConfig_t *DPPcfg) 
{
	char str[1000], str1[1000], *pread;
	int i, ch=-1, val, Off=0, tr = -1;
    int ret = 0;

    // Save previous valus (for compare)
    int PrevDesMode = DPPcfg->DesMode;
    int PrevUseCorrections = DPPcfg->useCorrections;
	int PrevUseManualTables = DPPcfg->UseManualTables;
    size_t TabBuf[sizeof(DPPcfg->TablesFilenames)];
    // Copy the filenames to watch for changes
    memcpy(TabBuf, DPPcfg->TablesFilenames, sizeof(DPPcfg->TablesFilenames));      

	/* Default settings */
	SetDefaultConfiguration(DPPcfg);

	/* read config file and assign parameters */
	while(!feof(f_ini)) {
		int read;
        char *res;
        // read a word from the file
        read = fscanf(f_ini, "%s", str);
        if( !read || (read == EOF) || !strlen(str))
			continue;
        // skip comments
        if(str[0] == '#') {
            res = fgets(str, 1000, f_ini);
			continue;
        }

        if (strcmp(str, "@ON")==0) {
            Off = 0;
            continue;
        }
		if (strcmp(str, "@OFF")==0)
            Off = 1;
        if (Off)
            continue;


        // Section (COMMON or individual channel)
		if (str[0] == '[') {
            if (strstr(str, "COMMON")) {
                ch = -1;
               continue; 
            }
            if (strstr(str, "TR")) {
				sscanf(str+1, "TR%d", &val);
				 if (val < 0 || val >= MAX_SET) {
                    printf("%s: Invalid channel number\n", str);
                } else {
                    tr = val;
                }
            } else {
                sscanf(str+1, "%d", &val);
                if (val < 0 || val >= MAX_SET) {
                    printf("%s: Invalid channel number\n", str);
                } else {
                    ch = val;
                }
            }
            continue;
		}
 
        // OPEN: read the details of physical path to the digitizer
		if (strstr(str, "OPEN")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "USB")==0)
				DPPcfg->LinkType = CAEN_DGTZ_USB;
			else if (strcmp(str1, "PCI")==0)
				DPPcfg->LinkType = CAEN_DGTZ_OpticalLink;
            else {
                printf("%s %s: Invalid connection type\n", str, str1);
				return -1; 
            }
			read = fscanf(f_ini, "%d", &DPPcfg->LinkNum);
            if (DPPcfg->LinkType == CAEN_DGTZ_USB)
                DPPcfg->ConetNode = 0;
            else
			    read = fscanf(f_ini, "%d", &DPPcfg->ConetNode);
			read = fscanf(f_ini, "%x", &DPPcfg->BaseAddress);
			continue;
		}

		// Generic VME Write (address offset + data + mask, each exadecimal)
		if ((strstr(str, "WRITE_REGISTER")!=NULL) && (DPPcfg->GWn < MAX_GW)) {
			read = fscanf(f_ini, "%x", (int *)&DPPcfg->GWaddr[DPPcfg->GWn]);
			read = fscanf(f_ini, "%x", (int *)&DPPcfg->GWdata[DPPcfg->GWn]);
            read = fscanf(f_ini, "%x", (int *)&DPPcfg->GWmask[DPPcfg->GWn]);
			DPPcfg->GWn++;
			continue;
		}

        // Acquisition Record Length (number of samples)
		if (strstr(str, "RECORD_LENGTH")!=NULL) {
			read = fscanf(f_ini, "%d", &DPPcfg->RecordLength);
			continue;
		}

        // Acquisition Record Length (number of samples)
		if (strstr(str, "DRS4_FREQUENCY")!=NULL) {
            int PrevDRS4Freq = DPPcfg->DRS4Frequency;
            int freq;
            read = fscanf(f_ini, "%d", &freq);
            DPPcfg->DRS4Frequency = (CAEN_DGTZ_DRS4Frequency_t)freq;
            if(PrevDRS4Freq != DPPcfg->DRS4Frequency)
                ret |= (0x1 << CFGRELOAD_CORRTABLES_BIT);
			continue;
		}

        // Correction Level (mask)
		if (strstr(str, "CORRECTION_LEVEL")!=NULL) {
            int changed = 0;
            
            read = fscanf(f_ini, "%s", str1);
            if( strcmp(str1, "AUTO") == 0 )
                DPPcfg->useCorrections = -1;
            else {
                int gr = 0;
                char Buf[1000];
                const char *tokens = " \t";
                char *ptr = Buf;

                DPPcfg->useCorrections = atoi(str1);
                pread = fgets(Buf, 1000, f_ini); // Get the remaining line
                DPPcfg->UseManualTables = -1;
                if(sscanf(ptr, "%s", str1) == 0) {
                    printf("Invalid syntax for parameter %s\n", str);
                    continue;
                }
                if(strcmp(str1, "AUTO") != 0) { // The user wants to use custom correction tables
                    DPPcfg->UseManualTables = atoi(ptr); // Save the group mask
                    ptr = strstr(ptr, str1);
                    ptr += strlen(str1);
                    while(sscanf(ptr, "%s", str1) == 1 && gr < MAX_X742_GROUP_SIZE) {
                        while( ((DPPcfg->UseManualTables) & (0x1 << gr)) == 0 && gr < MAX_X742_GROUP_SIZE)
                            gr++;
                        if(gr >= MAX_X742_GROUP_SIZE) {
                            printf("Error parsing values for parameter %s\n", str);
                            continue;
                        }
                        ptr = strstr(ptr, str1);
                        ptr += strlen(str1);
                        strcpy(DPPcfg->TablesFilenames[gr], str1);
                        gr++;
                    }
                }
            }

            // Check for changes
            if (PrevUseCorrections != DPPcfg->useCorrections)
                changed = 1;
            else if (PrevUseManualTables != DPPcfg->UseManualTables)
                changed = 1;
            else if (memcmp(TabBuf, DPPcfg->TablesFilenames, sizeof(DPPcfg->TablesFilenames)))
                changed = 1;
            if (changed == 1)
                ret |= (0x1 << CFGRELOAD_CORRTABLES_BIT);
			continue;
		}

        // Test Pattern
		if (strstr(str, "TEST_PATTERN")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "YES")==0)
				DPPcfg->TestPattern = 1;
			else if (strcmp(str1, "NO")!=0)
				printf("%s: invalid option\n", str);
			continue;
		}

		// Acquisition Record Length (number of samples)
		if (strstr(str, "DECIMATION_FACTOR")!=NULL) {
			read = fscanf(f_ini, "%d", &DPPcfg->DecimationFactor);
			continue;
		}

        // Trigger Edge
		if (strstr(str, "TRIGGER_EDGE")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "FALLING")==0)
				DPPcfg->TriggerEdge = 1;
			else if (strcmp(str1, "RISING")!=0)
				printf("%s: invalid option\n", str);
			continue;
		}

        // External Trigger (DISABLED, ACQUISITION_ONLY, ACQUISITION_AND_TRGOUT)
		if (strstr(str, "EXTERNAL_TRIGGER")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "DISABLED")==0)
                DPPcfg->ExtTriggerMode = CAEN_DGTZ_TRGMODE_DISABLED;
			else if (strcmp(str1, "ACQUISITION_ONLY")==0)
                DPPcfg->ExtTriggerMode = CAEN_DGTZ_TRGMODE_ACQ_ONLY;
			else if (strcmp(str1, "ACQUISITION_AND_TRGOUT")==0)
                DPPcfg->ExtTriggerMode = CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT;
            else
                printf("%s: Invalid Parameter\n", str);
            continue;
		}

        // Max. number of events for a block transfer (0 to 1023)
		if (strstr(str, "MAX_NUM_EVENTS_BLT")!=NULL) {
			read = fscanf(f_ini, "%d", &DPPcfg->NumEvents);
			continue;
		}

		// GNUplot path
		if (strstr(str, "GNUPLOT_PATH")!=NULL) {
			read = fscanf(f_ini, "%s", DPPcfg->GnuPlotPath);
			continue;
		}

		// Post Trigger (percent of the acquisition window)
		if (strstr(str, "POST_TRIGGER")!=NULL) {
			read = fscanf(f_ini, "%d", &DPPcfg->PostTrigger);
			continue;
		}

        // DesMode (Double sampling frequency for the Mod 731 and 751)
		if (strstr(str, "ENABLE_DES_MODE")!=NULL) {
            read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "YES")==0)
				DPPcfg->DesMode = 1;
			else if (strcmp(str1, "NO")!=0)
				printf("%s: invalid option\n", str);
            if(PrevDesMode != DPPcfg->DesMode)
                ret |= (0x1 << CFGRELOAD_DESMODE_BIT);
			continue;
		}

		// Output file format (BINARY or ASCII)
		if (strstr(str, "OUTPUT_FILE_FORMAT")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "BINARY")==0)
				DPPcfg->OutFileFlags|= OFF_BINARY;
			else if (strcmp(str1, "ASCII")!=0)
				printf("%s: invalid output file format\n", str1);
			continue;
		}

		// Header into output file (YES or NO)
		if (strstr(str, "OUTPUT_FILE_HEADER")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "YES")==0)
				DPPcfg->OutFileFlags|= OFF_HEADER;
			else if (strcmp(str1, "NO")!=0)
				printf("%s: invalid option\n", str);
			continue;
		}

        // Interrupt settings (request interrupt when there are at least N events to read; 0=disable interrupts (polling mode))
		if (strstr(str, "USE_INTERRUPT")!=NULL) {
			read = fscanf(f_ini, "%d", &DPPcfg->InterruptNumEvents);
			continue;
		}
		
		if (!strcmp(str, "FAST_TRIGGER")) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "DISABLED")==0)
                DPPcfg->FastTriggerMode = CAEN_DGTZ_TRGMODE_DISABLED;
			else if (strcmp(str1, "ACQUISITION_ONLY")==0)
                DPPcfg->FastTriggerMode = CAEN_DGTZ_TRGMODE_ACQ_ONLY;
            else
                printf("%s: Invalid Parameter\n", str);
            continue;
		}
		
		if (strstr(str, "ENABLED_FAST_TRIGGER_DIGITIZING")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "YES")==0)
				DPPcfg->FastTriggerEnabled= 1;
			else if (strcmp(str1, "NO")!=0)
				printf("%s: invalid option\n", str);
			continue;
		}
		
		// DC offset (percent of the dynamic range, -50 to 50)
		if (!strcmp(str, "DC_OFFSET")) {
            float dc;
			read = fscanf(f_ini, "%f", &dc);
			if (tr != -1) {
// 				DPPcfg->FTDCoffset[tr] = dc;
 				DPPcfg->FTDCoffset[tr*2] = (uint32_t)dc;
 				DPPcfg->FTDCoffset[tr*2+1] = (uint32_t)dc;
				continue;
			}
            val = (int)((dc+50) * 65535 / 100);
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->DCoffset[i] = val;
            else
                DPPcfg->DCoffset[ch] = val;
			continue;
		}
		
		if (strstr(str, "GRP_CH_DC_OFFSET")!=NULL) {
            float dc[8];
			read = fscanf(f_ini, "%f,%f,%f,%f,%f,%f,%f,%f", &dc[0], &dc[1], &dc[2], &dc[3], &dc[4], &dc[5], &dc[6], &dc[7]);
            for(i=0; i<MAX_SET; i++) {
				val = (int)((dc[i]+50) * 65535 / 100); 
				DPPcfg->DCoffsetGrpCh[ch][i] = val;
            }
			continue;
		}

		// Threshold
		if (strstr(str, "TRIGGER_THRESHOLD")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) {
//				DPPcfg->FTThreshold[tr] = val;
 				DPPcfg->FTThreshold[tr*2] = val;
 				DPPcfg->FTThreshold[tr*2+1] = val;

				continue;
			}
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->Threshold[i] = val;
            else
                DPPcfg->Threshold[ch] = val;
			continue;
		}

		// Group Trigger Enable Mask (hex 8 bit)
		if (strstr(str, "GROUP_TRG_ENABLE_MASK")!=NULL) {
			read = fscanf(f_ini, "%x", &val);
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->GroupTrgEnableMask[i] = val & 0xFF;
            else
                 DPPcfg->GroupTrgEnableMask[ch] = val & 0xFF;
			continue;
		}

        // Channel Auto trigger (DISABLED, ACQUISITION_ONLY, ACQUISITION_AND_TRGOUT)
		if (strstr(str, "CHANNEL_TRIGGER")!=NULL) {
            CAEN_DGTZ_TriggerMode_t tm;
			read = fscanf(f_ini, "%s", str1);
            if (strcmp(str1, "DISABLED")==0)
                tm = CAEN_DGTZ_TRGMODE_DISABLED;
            else if (strcmp(str1, "ACQUISITION_ONLY")==0)
                tm = CAEN_DGTZ_TRGMODE_ACQ_ONLY;
			else if (strcmp(str1, "ACQUISITION_AND_TRGOUT")==0)
                tm = CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT;
            else {
                printf("%s: Invalid Parameter\n", str);
                continue;
            }
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->ChannelTriggerMode[i] = tm;
            else
                DPPcfg->ChannelTriggerMode[ch] = tm;
		    continue;
		}

        // Front Panel LEMO I/O level (NIM, TTL)
		if (strstr(str, "FPIO_LEVEL")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "TTL")==0)
				DPPcfg->FPIOtype = 1;
			else if (strcmp(str1, "NIM")!=0)
				printf("%s: invalid option\n", str);
			continue;
		}

        // Channel Enable (or Group enable for the V1740) (YES/NO)
        if (strstr(str, "ENABLE_INPUT")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
            if (strcmp(str1, "YES")==0) {
                if (ch == -1)
                    DPPcfg->EnableMask = 0xFF;
                else
                    DPPcfg->EnableMask |= (1 << ch);
			    continue;
            } else if (strcmp(str1, "NO")==0) {
                if (ch == -1)
                    DPPcfg->EnableMask = 0x00;
                else
                    DPPcfg->EnableMask &= ~(1 << ch);
			    continue;
            } else {
                printf("%s: invalid option\n", str);
            }
			continue;
		}

        printf("%s: invalid setting\n", str);
	}
	return ret;
}

