import Hamlib
import time, subprocess, os, signal

Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

tuned_freq = -1
sdr_process = -1

# Init RIG_MODEL_DUMMY
rig = Hamlib.Rig(Hamlib.RIG_MODEL_NETRIGCTL)
rig.set_conf("rig_pathname", "127.0.0.1:4532")
rig.set_conf("retry", "5")

rig.open()

os.environ["CSDR_PRINT_BUFSIZES"] = "1"
os.environ["CSDR_DYNAMIC_BUFSIZE_ON"] = "1"

# config stuff
tuner_offset = 30000
sample_rate = 250000
gain = 40
audio_rate = 48000
tbw = 0.15
bandwidth = 3000
buffer_size = 4096

def sdr_command(freq):
    freq = int(freq)
    center = freq + tuner_offset
    shift = float(tuner_offset) / sample_rate
    decimation = float(sample_rate) / audio_rate
    first_stage_decimation = int(decimation)
    second_stage_decimation = decimation / first_stage_decimation
    intermediate_sample_rate = float(sample_rate) / first_stage_decimation
    bandpass_high_cut = float(bandwidth) / intermediate_sample_rate
    audio_buffer_size = buffer_size / decimation

    command = "rx_sdr -f {center} -s {sample_rate} -g 40 - -F CF32 -S | csdr setbuf {initial_buffer_size} | csdr shift_addition_cc {shift} | csdr fir_decimate_cc {first_stage_decimation} 0.005 HAMMING | csdr bandpass_fir_fft_cc 0 {bandpass_high_cut} 0.005 | csdr realpart_cf | csdr fractional_decimator_ff {second_stage_decimation} | csdr agc_ff | csdr limit_ff | csdr convert_f_s16 | ".format(
        center = center,
        sample_rate = sample_rate,
        shift = shift,
        decimation = decimation,
        first_stage_decimation = first_stage_decimation,
        second_stage_decimation = second_stage_decimation,
        bandpass_high_cut = bandpass_high_cut,
        initial_buffer_size = buffer_size
    )

    playback = "paplay -p --channels 1 --format s16le --rate {audio_rate} --raw --latency {audio_buffer_size}".format(
        audio_rate = audio_rate,
        audio_buffer_size = audio_buffer_size
    )

    playback = "aplay -t raw -c 1 -f S16_LE -r {audio_rate} -B 50000 -D {device} -q -".format(
        audio_rate = audio_rate,
        device = "hw:CARD=Loopback,DEV=0"
    )

    return command + playback

try:
    while True:
        freq = rig.get_freq()
        if freq != tuned_freq:
            if sdr_process != -1:
                print "terminating existing demodulator"
                os.killpg(os.getpgid(sdr_process.pid), signal.SIGTERM)
                time.sleep(1)
            print "frequency change: {}".format(freq)
            print sdr_command(freq)
            sdr_process = subprocess.Popen(sdr_command(freq), shell=True, preexec_fn = os.setsid)
            tuned_freq = freq
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    os.killpg(os.getpgid(sdr_process.pid), signal.SIGTERM)

#export CSDR_PRINT_BUFSIZES=1
#export CSDR_DYNAMIC_BUFSIZE_ON=1

#CENTER=7100000
#FREQ=7074000
#SRATE=250000
#DEVICE="plughw:CARD=ALSA,DEV=1"
##DEVICE="plughw:1,0"
#AUDIO_RATE=48000
#TBWR=0.15
#rx_sdr -s $SRATE -f $CENTER -g 40 - | csdr setbuf 2048 | csdr convert_u8_f | csdr shift_addition_cc `python -c "print float($CENTER-$FREQ)/$SRATE"` | csdr fir_decimate_cc `python -c "print float($SRATE)/float($AUDIO_RATE)"` `python -c "print float($TBWR)*(float($AUDIO_RATE)/float($SRATE))"` HAMMING | csdr bandpass_fir_fft_cc 0 0.0625 0.05 | csdr realpart_cf | csdr agc_ff | csdr limit_ff | csdr convert_f_s16 | aplay -t raw -c 1 -f S16_LE -r $AUDIO_RATE -B 50000 -D $DEVICE -q -





