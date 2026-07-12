import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export const TitleIntro: React.FC<{ title: string }> = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const words = title.split(' ').filter(Boolean);
  
  // High energy background
  const bgScale = spring({ fps, frame, config: { damping: 200 } });
  
  // Stomp words timing
  const staggerFrames = Math.max(3, Math.floor((durationInFrames - 30) / words.length)); 

  return (
    <AbsoluteFill style={{ 
      backgroundColor: '#111', 
      justifyContent: 'center', 
      alignItems: 'center',
      padding: '40px'
    }}>
      {/* Background kinetic effect */}
      <AbsoluteFill style={{
        backgroundImage: 'radial-gradient(circle at center, #333 0%, #111 100%)',
        opacity: interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' })
      }} />

      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '20px' }}>
        {words.map((word, i) => {
          const wordStart = i * staggerFrames;
          
          // Fast popping spring
          const wordScale = spring({
            fps,
            frame: frame - wordStart,
            config: { damping: 10, stiffness: 300, mass: 0.5 },
            durationInFrames: 10
          });

          // Pop out slightly at the end of the intro
          const outFade = interpolate(
            frame,
            [durationInFrames - 15, durationInFrames],
            [1, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );

          // Randomize rotation slightly for kinetic feel
          const rotation = i % 2 === 0 ? '-2deg' : '2deg';

          return (
            <div
              key={i}
              style={{
                transform: `scale(${wordScale}) rotate(${rotation})`,
                opacity: wordScale > 0 ? outFade : 0,
                color: '#FFF',
                fontFamily: 'Noto Sans Myanmar, Inter, sans-serif',
                fontWeight: 900,
                fontSize: '90px',
                lineHeight: 1.1,
                textTransform: 'uppercase',
                textShadow: '4px 4px 0px #E50914, -2px -2px 0px #00F0FF',
                margin: '10px 0'
              }}
            >
              {word}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
