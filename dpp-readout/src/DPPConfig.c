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
    /* TODO: need default values for new params */
    DPPcfg->RecordLength = (1024*16);
	DPPcfg->GWn = 0;
    DPPcfg->AcqMode = CAEN_DGTZ_DPP_ACQ_MODE_Oscilloscope;
    DPPcfg->PulsePolarity = CAEN_DGTZ_PulsePolarityPositive;
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


        /****Joey added****/
        // Pulse Polarity
		if (strstr(str, "PULSE_POLARITY")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "NEGATIVE")==0)
				DPPcfg->PulsePolarity = CAEN_DGTZ_PulsePolarityNegative;
			else if (strcmp(str1, "POSITIVE")!=0)
				printf("%s: invalid option\n", str);
			continue;
		}

        // Acquisition Mode (OSCILLOSCOPE, LIST, MIXED)
		if (strstr(str, "ACQUISITION_MODE")!=NULL) {
			read = fscanf(f_ini, "%s", str1);
			if (strcmp(str1, "OSCILLOSCOPE")==0)
                DPPcfg->AcqMode = CAEN_DGTZ_DPP_ACQ_MODE_Oscilloscope;
			else if (strcmp(str1, "LIST")==0)
                DPPcfg->AcqMode = CAEN_DGTZ_DPP_ACQ_MODE_List;
			else if (strcmp(str1, "MIXED")==0)
                DPPcfg->AcqMode = CAEN_DGTZ_DPP_ACQ_MODE_Mixed;
            else
                printf("%s: Invalid Parameter\n", str);
            continue;
		}

		// Threshold
		if (strstr(str, "TRIGGER_THRESHOLD")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->Threshold[i] = val;
            else
                DPPcfg->Threshold[ch] = val;
			continue;
		}

        ////////////////////
        /* DPP Parameters */
        ////////////////////
		// Trap rise time
		if (strstr(str, "TRAPEZOID_RISE_TIME")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->TrapRiseTime[i] = val;
            else
                DPPcfg->TrapRiseTime[ch] = val;
			continue;
		}

		// Trap flat top
		if (strstr(str, "TRAPEZOID_FLAT_TOP")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->TrapFlatTop[i] = val;
            else
                DPPcfg->TrapFlatTop[ch] = val;
			continue;
		}

		// Decay time constant
		if (strstr(str, "DECAY_TIME_CONSTANT")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->DecayTimeConstant[i] = val;
            else
                DPPcfg->DecayTimeConstant[ch] = val;
			continue;
		}


		// Peaking time
		if (strstr(str, "PEAKING_TIME")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->PeakingTime[i] = val;
            else
                DPPcfg->PeakingTime[ch] = val;
			continue;
		}

		// Trigger filter smoothing factor
		if (strstr(str, "TRIGGER_SMOOTHING_FACTOR")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->TriggerSmoothingFactor[i] = val;
            else
                DPPcfg->TriggerSmoothingFactor[ch] = val;
			continue;
		}

		// Signal rise time
		if (strstr(str, "SIGNAL_RISE_TIME")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->SignalRiseTime[i] = val;
            else
                DPPcfg->SignalRiseTime[ch] = val;
			continue;
		}

		if (strstr(str, "TRIGGER_HOLDOFF")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->TriggerHoldoff[i] = val;
            else
                DPPcfg->TriggerHoldoff[ch] = val;
			continue;
		}

        // number of samples for baseline average calculation. Options: 1->16 samples; 2->64 samples; 3->256 samples; 4->1024 samples; 5->4096 samples; 6->16384 samples
		if (strstr(str, "BASELINE_SAMPLES")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->BaselineSamples[i] = val;
            else
                DPPcfg->BaselineSamples[ch] = val;
			continue;
		}

		if (strstr(str, "TRAPEZOID_SMOOTHING")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->TrapSmoothing[i] = val;
            else
                DPPcfg->TrapSmoothing[ch] = val;
			continue;
		}

		if (strstr(str, "PEAK_HOLDOFF")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->PeakHoldoff[i] = val;
            else
                DPPcfg->PeakHoldoff[ch] = val;
			continue;
		}


		if (strstr(str, "BASELINE_HOLDOFF")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->BaselineHoldoff[i] = val;
            else
                DPPcfg->BaselineHoldoff[ch] = val;
			continue;
		}

		if (strstr(str, "ENERGY_NORMALIZATION")!=NULL) {
            float enorm;
			read = fscanf(f_ini, "%f", &enorm);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->EnergyNormalization[i] = enorm;
            else
                DPPcfg->EnergyNormalization[ch] = enorm;
			continue;
		}

		if (strstr(str, "DECIMATION")!=NULL) {
			read = fscanf(f_ini, "%d", &val);
			if (tr != -1) continue;
            if (ch == -1)
                for(i=0; i<MAX_SET; i++)
                    DPPcfg->Decimation[i] = val;
            else
                DPPcfg->Decimation[ch] = val;
			continue;
		}
        /////////////////////////////////////


		// Group Trigger Enable Mask (hex 8 bit)
		if (strstr(str, "GROUP_TRG_ENABLE_MASK")!=NULL) {
			read = fscanf(f_ini, "%x", &val);
            DPPcfg->GroupTrgEnableMask = val & 0xFF;
			continue;
		}


        printf("%s: invalid setting\n", str);
	}
	return ret;
}

