import React from 'react';
import {AbsoluteFill, Composition, Img, Sequence, registerRoot, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Reel, type ReelProps} from '../src/Reel';
import type {Shot} from '../src/types';

// Studio footage uses the workspace's outlined captions, without word cards.
const StudioCaptions: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  let cursor = 0;
  const pages = (shot.captionPages ?? [shot.say]).map(text => {
    const words = shot.words.slice(cursor, cursor + text.trim().split(/\s+/).length);
    cursor += words.length;
    return {text, start: words[0]?.start ?? 0};
  });
  const page = pages.findLast(p => p.start <= frame / fps);
  if (!page) return null;
  return <div style={{position:'absolute',top:1450,left:85,right:85,textAlign:'center',
    fontFamily:'StudioInter, sans-serif',fontWeight:850,fontSize:64,lineHeight:1.15,
    color:'#ffffff',WebkitTextStroke:'2.5px #10131b',paintOrder:'stroke fill',
    textShadow:'0 3px 8px #000a'}}>{page.text}</div>;
};

const StudioReel: React.FC<ReelProps> = ({slug, reel}) => {
  if (!reel) throw new Error('Studio reel data is missing');
  const clean = {...reel,shots:reel.shots.map(shot => ({...shot,captions:false}))};
  return <AbsoluteFill>
    <Reel slug={slug} reel={clean}/>
    {reel.shots.filter(shot => shot.studioTextImage).map(shot =>
      <Sequence key={'text-'+shot.id} from={shot.from} durationInFrames={shot.frames}>
        <Img src={staticFile(shot.studioTextImage!)} style={{position:'absolute',inset:0,width:1080,height:1920}}/>
      </Sequence>)}
    {reel.shots.filter(shot => shot.captions !== false).map(shot =>
      <Sequence key={shot.id} from={shot.from} durationInFrames={shot.frames}>
        <StudioCaptions shot={shot}/>
      </Sequence>)}
  </AbsoluteFill>;
};

const Root = () => <Composition id="StudioReel" component={StudioReel}
  defaultProps={{slug:'studio',reel:null}} fps={30} width={1080} height={1920}
  durationInFrames={1} calculateMetadata={({props}) => ({
    durationInFrames: Math.max(1, props.reel?.durationInFrames ?? 1),
  })}/>;
registerRoot(Root);
