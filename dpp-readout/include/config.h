/*******
 * This is mostly taken from:
 * https://github.com/cjpl/caen-suite/blob/master/WaveDump/inc/WaveDump.h
 * I assumed a linux dist and am probably including lots of things that
 * are unused.. clean up later?
 * (Joey 2022/09/20)
 */

#ifndef _DPPCONFIG__H
#define _DPPCONFIG__H


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
//#include <fstream.h>
#include <CAENDigitizer.h>
#include <CAENDigitizerType.h>


#include <unistd.h>
#include <stdint.h>   /* C99 compliant compilers: uint64_t */
#include <ctype.h>    /* toupper() */
#include <sys/time.h>

#define		_PACKED_		__attribute__ ((packed, aligned(1)))
#define		_INLINE_		__inline__ 

#define DEFAULT_CONFIG_FILE  "/etc/wavedump/default_config"
#define GNUPLOT_DEFAULT_PATH ""



#define OUTFILENAME "wave"  /* The actual file name is wave_n.txt, where n is the channel */
#define MAX_CH  64          /* max. number of channels */
#define MAX_SET 16           /* max. number of independent settings */

#define MAX_GW  1000        /* max. number of generic write commads */

#define PLOT_REFRESH_TIME 1000

#define VME_INTERRUPT_LEVEL      1
#define VME_INTERRUPT_STATUS_ID  0xAAAA
#define INTERRUPT_MODE           CAEN_DGTZ_IRQ_MODE_ROAK
#define INTERRUPT_TIMEOUT        200  // ms
        
#define PLOT_WAVEFORMS   0
#define PLOT_FFT         1
#define PLOT_HISTOGRAM   2

#define CFGRELOAD_CORRTABLES_BIT (0)
#define CFGRELOAD_DESMODE_BIT (1)



/* ###########################################################################
   Typedefs
   ###########################################################################
*/

typedef enum {
	OFF_BINARY=	0x00000001,			// Bit 0: 1 = BINARY, 0 =ASCII
	OFF_HEADER= 0x00000002,			// Bit 1: 1 = include header, 0 = just samples data
} OUTFILE_FLAGS;


typedef struct {
    int LinkType;
    int LinkNum;
    int ConetNode;
    uint32_t BaseAddress;
    int Nch;
    int Nbit;
    float Ts;
    int RecordLength;
    CAEN_DGTZ_PulsePolarity_t PulsePolarity;
    CAEN_DGTZ_DPP_AcqMode_t AcqMode;
    uint32_t Threshold[MAX_SET];
    uint32_t TrapRiseTime[MAX_SET];
    uint32_t TrapFlatTop[MAX_SET];
    uint32_t DecayTimeConstant[MAX_SET];
    uint32_t PeakingTime[MAX_SET];
    uint32_t TriggerSmoothingFactor[MAX_SET];
    uint32_t SignalRiseTime[MAX_SET];
    uint32_t TriggerHoldoff[MAX_SET];

    uint32_t BaselineSamples[MAX_SET];
    uint32_t TrapSmoothing[MAX_SET];
    uint32_t PeakHoldoff[MAX_SET];
    uint32_t BaselineHoldoff[MAX_SET];
    float EnergyNormalization[MAX_SET];
    uint32_t Decimation[MAX_SET];

	uint8_t GroupTrgEnableMask;
    int GWn;
    uint32_t GWaddr[MAX_GW];
    uint32_t GWdata[MAX_GW];
	uint32_t GWmask[MAX_GW];
} DPPConfig_t;



/* Function prototypes */
int ParseConfigFile(FILE *f_ini, DPPConfig_t *DPPcfg);


#endif /* _DPPConfig__H */
