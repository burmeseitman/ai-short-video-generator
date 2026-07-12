import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(1);

// Allow loading local file:// URIs generated outside the public folder
Config.setChromiumOpenGlRenderer('swangle'); // Use software rendering to prevent Chromium decode timeout on headless VMs
Config.setChromiumDisableWebSecurity(true);
