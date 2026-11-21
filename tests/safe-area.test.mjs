import { test } from 'node:test';
import assert from 'node:assert/strict';
import { getSafeArea, PLATFORMS, validateBox, renderSafeAreaToolbar, renderSimulatedUI, renderSafeAreaGuides } from '../dashboard/safe-area.mjs';

test('getSafeArea calculates correct platform bounds and normalized ratios on 1080x1920', () => {
  const universal = getSafeArea('universal', 1080, 1920);
  assert.equal(universal.platform, 'universal');
  assert.equal(universal.topPx, 290);
  assert.equal(universal.bottomPx, 440);
  assert.equal(universal.leftPx, 70);
  assert.equal(universal.rightPx, 160);
  assert.equal(universal.safeWidthPx, 850);
  assert.equal(universal.safeHeightPx, 1190);
  assert.equal(universal.safeXMaxPx, 920);
  assert.equal(universal.safeYMaxPx, 1480);

  const instagram = getSafeArea('instagram', 1080, 1920);
  assert.equal(instagram.platform, 'instagram');
  assert.equal(instagram.topPx, 220);
  assert.equal(instagram.bottomPx, 380);
  assert.equal(instagram.leftPx, 60);
  assert.equal(instagram.rightPx, 130);
  assert.equal(instagram.safeWidthPx, 890);
  assert.equal(instagram.safeHeightPx, 1320);

  const tiktok = getSafeArea('tiktok', 1080, 1920);
  assert.equal(tiktok.platform, 'tiktok');
  assert.equal(tiktok.topPx, 240);
  assert.equal(tiktok.bottomPx, 440);
  assert.equal(tiktok.leftPx, 60);
  assert.equal(tiktok.rightPx, 150);

  const youtube = getSafeArea('youtube', 1080, 1920);
  assert.equal(youtube.platform, 'youtube');
  assert.equal(youtube.topPx, 280);
  assert.equal(youtube.bottomPx, 400);
  assert.equal(youtube.leftPx, 60);
  assert.equal(youtube.rightPx, 160);

  const off = getSafeArea('off', 1080, 1920);
  assert.equal(off.platform, 'off');
  assert.equal(off.topPx, 0);
  assert.equal(off.bottomPx, 0);
  assert.equal(off.safeWidthPct, 100);
});

test('getSafeArea scales accurately for 4K UHD 2160x3840 canvas', () => {
  const sa4k = getSafeArea('universal', 2160, 3840);
  assert.equal(sa4k.width, 2160);
  assert.equal(sa4k.height, 3840);
  assert.equal(sa4k.topPx, 290 * 2);
  assert.equal(sa4k.bottomPx, 440 * 2);
  assert.equal(sa4k.leftPx, 70 * 2);
  assert.equal(sa4k.rightPx, 160 * 2);
  assert.equal(sa4k.safeWidthPx, 850 * 2);
  assert.equal(sa4k.safeHeightPx, 1190 * 2);
});

test('validateBox detects danger zone violations and clamps coordinates safely', () => {
  // Element placed too high in top restricted zone (y=100 on 1920)
  const topOverflow = validateBox({ x: 200, y: 100, width: 400, height: 100 }, 'universal', 1080, 1920);
  assert.equal(topOverflow.valid, false);
  assert.ok(topOverflow.violations.some(v => v.includes('Top overflow')));
  assert.equal(topOverflow.clamped.y, 290);

  // Element placed too low in bottom restricted zone (y=1600 on 1920)
  const bottomOverflow = validateBox({ x: 200, y: 1600, width: 400, height: 100 }, 'universal', 1080, 1920);
  assert.equal(bottomOverflow.valid, false);
  assert.ok(bottomOverflow.violations.some(v => v.includes('Bottom overflow')));
  assert.equal(bottomOverflow.clamped.y, 1480 - 100);

  // Element crossing right action rail (x=850, width=200 -> x+w=1050 > 920)
  const rightOverflow = validateBox({ x: 850, y: 500, width: 200, height: 100 }, 'universal', 1080, 1920);
  assert.equal(rightOverflow.valid, false);
  assert.ok(rightOverflow.violations.some(v => v.includes('Right overflow')));
  assert.equal(rightOverflow.clamped.x, 920 - 200);

  // Valid element cleanly inside safe zone
  const validBox = validateBox({ x: 100, y: 350, width: 700, height: 300 }, 'universal', 1080, 1920);
  assert.equal(validBox.valid, true);
  assert.equal(validBox.violations.length, 0);

  // Normalized coordinates test
  const normalizedValid = validateBox({ x: 0.15, y: 0.20, width: 0.60, height: 0.40 }, 'universal', 1080, 1920);
  assert.equal(normalizedValid.valid, true);
});

test('renderSimulatedUI generates valid markup for all supported platforms', () => {
  for (const platform of ['instagram', 'tiktok', 'youtube', 'universal']) {
    const html = renderSimulatedUI(platform, 'Techno Ravan');
    assert.ok(typeof html === 'string');
    assert.ok(html.length > 50, `Markup for ${platform} should not be empty`);
    assert.ok(html.includes('safe-sim-ui'));
  }
  assert.equal(renderSimulatedUI('off'), '');
});

test('renderSafeAreaGuides generates boundary boxes and danger zones', () => {
  const guides = renderSafeAreaGuides('universal', true, true);
  assert.ok(guides.includes('safe-guides-layer'));
  assert.ok(guides.includes('safe-danger-zone top-zone'));
  assert.ok(guides.includes('safe-danger-zone bottom-zone'));
  assert.ok(guides.includes('safe-danger-zone right-zone'));
  assert.ok(guides.includes('safe-content-box'));
  assert.ok(guides.includes('safe-profile-grid-crop'));

  assert.equal(renderSafeAreaGuides('universal', false), '');
  assert.equal(renderSafeAreaGuides('off', true), '');
});

test('renderSafeAreaToolbar contains all platform buttons and options', () => {
  const toolbar = renderSafeAreaToolbar('universal', { showGuides: true, showSimUi: true, showProfileGrid: false });
  assert.ok(toolbar.includes('data-platform="universal"'));
  assert.ok(toolbar.includes('data-platform="instagram"'));
  assert.ok(toolbar.includes('data-platform="tiktok"'));
  assert.ok(toolbar.includes('data-platform="youtube"'));
  assert.ok(toolbar.includes('data-platform="off"'));
  assert.ok(toolbar.includes('id="safe-toggle-guides"'));
  assert.ok(toolbar.includes('id="safe-toggle-ui"'));
  assert.ok(toolbar.includes('id="safe-toggle-grid"'));
});
