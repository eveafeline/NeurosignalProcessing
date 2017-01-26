fileName = ''
rawFileName = ''

fs = 0
invert = False
timeDelay= 0 # time delay between trigger and stimulation
thres_up = 0 # threshold to detect rising edge
thres_down = 0 # threshold to detect falling edge
pre_stim = 0 # time before stimulation to start stimulation window
post_stim = 0 # time after stimulation to end stimulation window
order = 0 # filter order
maxReadTime = 0
maxRows = 0

f_high = 0
f_low = 0

dataValues = []
dataTimes = []
triggerValues = []
rawDataValues = []
dataFiltValues = []

stimTimeIdx = []
triggerTimeIdx = []
stimTimes = []
dataStimValues = []

whichStims = []

pulse_width = ''
i_stim = ''

yMin = 0
yMax = 0
xMin = 0
xMax = 0

