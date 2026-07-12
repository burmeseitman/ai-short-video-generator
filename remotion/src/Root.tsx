import { Composition } from 'remotion';
import { MainVideo } from './MainVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MainVideo"
        component={MainVideo}
        durationInFrames={1800} // Default. Overridden by calculateMetadata
        calculateMetadata={({ props }) => {
          return {
            durationInFrames: props.totalDurationFrames || 1800,
          };
        }}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          title: "Awesome Video",
          scenes: [],
          bgmPath: '',
          totalDurationFrames: 1800
        }}
      />
    </>
  );
};
