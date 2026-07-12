import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

export const DynamicSubtitle: React.FC<{ text: string; durationFrames: number }> = ({ text, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Split text by spaces to get chunks (works for English and space-delimited Myanmar)
  const words = text.split(' ').filter(Boolean);
  
  if (words.length === 0) return null;

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'center',
      gap: '12px 16px',
      backgroundColor: 'rgba(0, 0, 0, 0.65)',
      padding: '25px 40px',
      borderRadius: '25px',
      maxWidth: '90%',
      backdropFilter: 'blur(10px)',
      border: '2px solid rgba(255,255,255,0.1)'
    }}>
      {words.map((word, i) => {
        // Calculate when this word should appear
        const wordStartFrame = (i / words.length) * durationFrames * 0.8; // finish revealing at 80% of scene
        
        // Pop-in animation for the word
        const scale = spring({
          fps,
          frame: frame - wordStartFrame,
          config: { damping: 12, stiffness: 200 },
          durationInFrames: 10
        });

        // Opacity animation
        const opacity = interpolate(
          frame - wordStartFrame,
          [0, 5],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        // Highlight color if it's the "current" word being spoken (roughly)
        const wordEndFrame = ((i + 1) / words.length) * durationFrames * 0.8;
        const isCurrentWord = frame >= wordStartFrame && frame < wordEndFrame;
        
        // Color transition
        const color = isCurrentWord ? '#FFD700' : 'white';
        const textShadow = isCurrentWord 
          ? '0 0 15px rgba(255, 215, 0, 0.6), 2px 2px 4px rgba(0,0,0,0.8)' 
          : '2px 2px 4px rgba(0,0,0,0.8)';

        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              transform: `scale(${Math.max(0, scale)})`,
              opacity,
              color,
              fontFamily: 'Noto Sans Myanmar, sans-serif',
              fontWeight: 'bold',
              fontSize: '56px',
              textShadow,
              transition: 'color 0.2s ease-out, text-shadow 0.2s ease-out'
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
