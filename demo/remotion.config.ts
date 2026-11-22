import { Config } from '@remotion/cli/config'

Config.setVideoImageFormat('jpeg')
Config.setOverwriteOutput(true)
// most cores, leaving some for the ffmpeg that OffthreadVideo uses to pull frames
Config.setConcurrency('75%')
