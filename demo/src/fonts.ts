import { loadFont as loadSans } from '@remotion/google-fonts/IBMPlexSans'
import { loadFont as loadMono } from '@remotion/google-fonts/IBMPlexMono'
import { loadFont as loadDisplay } from '@remotion/google-fonts/InterTight'

loadSans('normal', { weights: ['400', '500', '600'], subsets: ['latin'] })
loadMono('normal', { weights: ['400', '500'], subsets: ['latin'] })
loadDisplay('normal', { weights: ['600'], subsets: ['latin'] })
