import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync,symlinkSync,existsSync,realpathSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {installDemo} from '../scripts/install-demo.mjs';
import {listProjects} from '../scripts/dashboard-library.mjs';

function fixture(t){
 const root=realpathSync(mkdtempSync(join(tmpdir(),'ravan-demo-')));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const put=(name,value)=>{const path=join(root,name);mkdirSync(dirname(path),{recursive:true});writeFileSync(path,value);return path;};
 put('examples/demo/README.md','Synthetic example');put('examples/demo/export.json',JSON.stringify({synthetic:true,file:'export/demo.mp4',cover:{png:'export/cover.png'}}));
 put('examples/demo/export/demo.mp4','video fixture');put('examples/demo/export/cover.png','cover fixture');put('examples/demo/export/caption.txt','Synthetic posting copy');put('examples/demo/private.MOV','MUST_NOT_COPY');
 return {root,put};
}
test('installs only fixed synthetic files and discovers video, cover and posting copy',t=>{
 const {root}=fixture(t),result=installDemo(root);assert.equal(result.project,'synthetic-demo');
 assert.equal(existsSync(join(result.folder,'private.MOV')),false);
 const [project]=listProjects(root);assert.equal(project.id,'synthetic-demo');assert.ok(project.primary);assert.ok(project.cover);assert.equal(project.captions.length,1);
 assert.equal(JSON.parse(readFileSync(join(result.folder,'export.json'))).synthetic,true);
});
test('never overwrites an existing project',t=>{
 const {root,put}=fixture(t);put('outputs/reels/synthetic-demo/original.txt','KEEP');
 assert.throws(()=>installDemo(root),/already exists/);assert.equal(readFileSync(join(root,'outputs/reels/synthetic-demo/original.txt'),'utf8'),'KEEP');
});
test('rejects symlink assets and output folders before copying',t=>{
 const {root}=fixture(t);rmSync(join(root,'examples/demo/export/demo.mp4'));symlinkSync(join(root,'examples/demo/export/caption.txt'),join(root,'examples/demo/export/demo.mp4'));
 assert.throws(()=>installDemo(root),/symlinks/);assert.equal(existsSync(join(root,'outputs')),false);
 const other=fixture(t);symlinkSync(join(other.root,'examples'),join(other.root,'outputs'));
 assert.throws(()=>installDemo(other.root),/symlinks/);
});
