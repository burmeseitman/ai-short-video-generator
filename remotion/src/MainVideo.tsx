import React, { useMemo } from 'react';
import { AbsoluteFill, Audio, Sequence, interpolate, useCurrentFrame, useVideoConfig, Img, staticFile, OffthreadVideo } from 'remotion';

import { DynamicSubtitle } from './DynamicSubtitle';
import { TitleIntro } from './TitleIntro';

// --- Types ---
type SceneProps = {
  videoPath: string;
  voicePath: string;
  durationFrames: number;
  text: string;
  creditText?: string;
};

type MainVideoProps = {
  title?: string;
  totalDurationFrames: number;
  bgmPath: string;
  scenes: SceneProps[];
};

// --- Scene Component ---
const SceneComp: React.FC<{ scene: SceneProps }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Ken Burns zoom effect (1.0 to 1.1 over the scene duration)
  const scale = interpolate(frame, [0, scene.durationFrames], [1, 1.1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: 'black', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
        {scene.videoPath.endsWith('.jpg') || scene.videoPath.endsWith('.png') ? (
           <Img src={staticFile(scene.videoPath)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
           <OffthreadVideo 
             src={staticFile(scene.videoPath)} 
             style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
             muted 
           />
        )}
      </AbsoluteFill>
      
      {/* Voiceover */}
      {scene.voicePath && <Audio src={staticFile(scene.voicePath)} />}
      
      {/* Subtitles (Animated Word-by-Word) */}
      <AbsoluteFill style={{ justifyContent: 'flex-end', paddingBottom: '15%', alignItems: 'center' }}>
        <DynamicSubtitle text={scene.text} durationFrames={scene.durationFrames} />
      </AbsoluteFill>

      {/* Credit Text */}
      {scene.creditText && (
        <AbsoluteFill style={{ justifyContent: 'flex-start', alignItems: 'flex-end', padding: 30 }}>
          <div style={{
             backgroundColor: 'rgba(0, 0, 0, 0.6)',
             color: 'white',
             fontSize: 32,
             padding: '10px 20px',
             borderRadius: 10
          }}>
            {scene.creditText}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

// --- Main Composition ---
export const MainVideo: React.FC<MainVideoProps> = ({ title = "Awesome Video", scenes, bgmPath }) => {
  // Intro Sequence duration
  const introFrames = 90; // 3 seconds at 30fps

  // Disable overlap (crossfade) to save memory and prevent Chromium crashes
  const overlapFrames = 0; 
  
  const sceneStarts = useMemo(() => {
    let currentStart = introFrames; // Start scenes AFTER the intro
    const starts: number[] = [];
    for (const scene of scenes) {
      starts.push(currentStart);
      currentStart += (scene.durationFrames - overlapFrames);
    }
    return starts;
  }, [scenes, introFrames]);

  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      {/* Intro Sequence */}
      <Sequence from={0} durationInFrames={introFrames}>
        <TitleIntro title={title} />
      </Sequence>

      {/* Main Scenes */}
      {scenes.map((scene, index) => {
        const startFrame = sceneStarts[index];
        // The duration of the sequence is the actual duration of the scene
        return (
          <Sequence key={index} from={startFrame} durationInFrames={scene.durationFrames}>
            {/* Simple fade-in transition for scenes after the first one */}
            <FadeInTransition fadeFrames={index === 0 ? 0 : overlapFrames}>
              <SceneComp scene={scene} />
            </FadeInTransition>
          </Sequence>
        );
      })}

      {/* Background Music */}
      {bgmPath && <Audio src={staticFile(bgmPath)} volume={0.15} loop />}
    </AbsoluteFill>
  );
};

// --- Transition Wrapper ---
const FadeInTransition: React.FC<{ fadeFrames: number; children: React.ReactNode }> = ({ fadeFrames, children }) => {
  const frame = useCurrentFrame();
  const opacity = fadeFrames > 0 ? interpolate(frame, [0, fadeFrames], [0, 1], { extrapolateRight: 'clamp' }) : 1;
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};
