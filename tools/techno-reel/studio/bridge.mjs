// Local studio adapter. The Python workflow owns preparation and approval checks.
import {bundle} from '@remotion/bundler';
import {renderStill, renderMedia, selectComposition} from '@remotion/renderer';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const engine = fileURLToPath(new URL('..', import.meta.url));
process.chdir(engine);
const input = JSON.parse(readFileSync(resolve(process.argv[2]), 'utf8'));
if (!['preview', 'render'].includes(input.mode)) throw Error('Unknown bridge mode');
const browserExecutable = process.env.REEL_BROWSER || undefined;
const serveUrl = await bundle({entryPoint:resolve('studio/index.tsx'), publicDir:input.publicDir});
const inputProps = {slug:'studio', reel:input.reel};
const composition = await selectComposition({serveUrl,id:'StudioReel',inputProps,browserExecutable});
if (input.mode === 'preview') {
  for (const job of input.jobs) {
    const props = structuredClone(inputProps);
    if (job.image) props.reel.shots.find(s => s.id === job.shot).studioPreview = job.image;
    // Remotion renders resolved composition.props; keep the still override there too.
    await renderStill({serveUrl,composition:{...composition,props},inputProps:props,frame:job.frame,
      output:job.output,scale:0.5,imageFormat:'png',browserExecutable});
    console.log(`Preview ${job.shot} frame ${job.frame}`);
  }
} else {
  await renderMedia({serveUrl,composition,inputProps,codec:'h264',crf:18,
    outputLocation:input.output,browserExecutable,concurrency:2,
    onProgress:({progress})=>{if(progress===1) console.log('Render complete');}});
}
