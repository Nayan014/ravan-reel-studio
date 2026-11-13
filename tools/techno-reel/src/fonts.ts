// Studio adaptation: bundled licensed fonts, no Google Fonts network requests.
import {staticFile, delayRender, continueRender, cancelRender} from "remotion";
const localFont = (name: string, file: string, weight: string) => {
  if (typeof document !== "undefined") {
    const handle = delayRender(`Loading ${name}`);
    const font = new FontFace(name, `url("${staticFile(`fonts/${file}`)}")`, {weight});
    font.load().then(f => {(document.fonts as FontFaceSet & {add(font: FontFace): void}).add(f); continueRender(handle);}).catch(cancelRender);
  }
  return name;
};
export const display = localFont("StudioAnton", "Anton-Regular.ttf", "400");
export const body = localFont("StudioInter", "Inter.ttf", "100 900");
// Print uses the bundled Archivo Black fallback; Flat Clay retains Anton and Inter.
export const paperDisplay = localFont("StudioPaper", "ArchivoBlack-Regular.ttf", "400");
