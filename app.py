import json, re, subprocess, tempfile
from pathlib import Path
import streamlit as st

st.set_page_config(page_title='ClipForge', page_icon='🎬', layout='wide')
st.title('🎬 ClipForge — YouTube to Shorts')
st.caption('Mobile-friendly clip maker • Use only videos you own or have permission to edit. Free hosting is best for short source videos.')

def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-1800:])
    return p.stdout

def duration(path):
    return float(json.loads(run(['ffprobe','-v','quiet','-show_format','-of','json',str(path)]))['format']['duration'])

def transcribe(path,model_name):
    from faster_whisper import WhisperModel
    model=WhisperModel(model_name,device='cpu',compute_type='int8')
    segments,_=model.transcribe(str(path),vad_filter=True,word_timestamps=True)
    return list(segments)

def candidates(segments,clip_len,limit,total):
    hooks=('how','why','secret','never','best','worst','crazy','actually','mistake','important','believe','wait','imagine','truth','first','problem','money','learn','what')
    rows=[]
    for seg in segments:
        start=max(0,float(seg.start)-1.5)
        end=min(total,start+clip_len)
        if end-start<min(10,clip_len*.6):continue
        words=' '.join(s.text for s in segments if s.start<end and s.end>start)
        score=sum(2 for h in hooks if re.search(r'\b'+h+r'\b',words.lower())) + min(len(words.split())/35,5)
        score+=min(words.count('?')*1.5,4)+min(words.count('!'),3)
        rows.append((score,start,end,words))
    rows.sort(reverse=True)
    chosen=[]
    for row in rows:
        if all(min(row[2],x[2])-max(row[1],x[1])<clip_len*.35 for x in chosen):
            chosen.append(row)
        if len(chosen)>=limit:break
    return sorted(chosen,key=lambda x:x[1])

def make_srt(segments,start,end,path):
    def ts(t):
        ms=int(max(0,t)*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    lines=[];idx=0
    for seg in segments:
        for w in (seg.words or []):
            if w.end<=start or w.start>=end:continue
            idx+=1
            lines.append(f'{idx}\n{ts(max(0,w.start-start))} --> {ts(min(end-start,w.end-start))}\n{w.word.strip()}\n')
    path.write_text('\n'.join(lines),encoding='utf-8')

url=st.text_input('YouTube URL (only content you are authorized to download)')
upload=st.file_uploader('Or upload an MP4 / MOV / MKV',type=['mp4','mov','mkv','m4v'])
col1,col2,col3=st.columns(3)
with col1: clip_len=st.slider('Clip length (seconds)',15,90,35,5)
with col2: count=st.slider('Number of clips',1,5,2)
with col3: model=st.selectbox('Transcription model',['tiny','base'],index=0)
captions=st.checkbox('Burn word-by-word subtitles',value=False)
if st.button('Generate clips',type='primary'):
    if not upload and not url:st.error('Upload a video or paste a YouTube URL.');st.stop()
    try:
        with st.spinner('Preparing video and transcribing speech — first run downloads the speech model.'):
            root=Path(tempfile.mkdtemp(prefix='clipforge_'))
            source=root/'source.mp4'
            if upload:
                if upload.size > 150*1024*1024: raise RuntimeError('Free hosting limit: upload a video smaller than 150 MB.')
                source.write_bytes(upload.getvalue())
            else:
                run(['yt-dlp','--no-playlist','-f','bv*+ba/b','--merge-output-format','mp4','-o',str(source),url])
                if not source.exists():
                    matches=list(root.glob('source.*'))
                    if not matches:raise RuntimeError('Video download failed')
                    source=matches[0]
            total=duration(source)
            if total > 900: raise RuntimeError('Free tier safety limit: source video must be 15 minutes or less. Trim the original first.')
            segments=transcribe(source,model)
            if not segments:raise RuntimeError('No speech detected. Try another video.')
            picks=candidates(segments,clip_len,count,total)
            if not picks:raise RuntimeError('No suitable clip windows found.')
            results=[]
            for i,(score,start,end,words) in enumerate(picks,1):
                output=root/f'clip_{i:02}.mp4';srt=root/f'clip_{i:02}.srt'
                make_srt(segments,start,end,srt)
                vf='scale=540:960:force_original_aspect_ratio=increase,crop=540:960'
                if captions:
                    # FFmpeg subtitles filter requires libass; escape special path characters.
                    escaped=str(srt).replace('\\','\\\\').replace(':','\\:').replace("'","\\'")
                    vf+=f",subtitles='{escaped}':force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Alignment=2,MarginV=170'"
                run(['ffmpeg','-y','-ss',str(start),'-i',str(source),'-t',str(end-start),'-vf',vf,'-c:v','libx264','-preset','ultrafast','-crf','23','-c:a','aac','-movflags','+faststart',str(output)])
                results.append((output,start,end,score,words))
            st.session_state['results']=[(p.name,p.read_bytes(),a,b,s,t) for p,a,b,s,t in results]
        st.success(f'Generated {len(results)} clips!')
    except Exception as exc:st.error(f'Processing error: {exc}')
for name,data,start,end,score,words in st.session_state.get('results',[]):
    st.subheader(f'{name} · {start:.0f}s–{end:.0f}s · heuristic score {score:.1f}')
    st.video(data)
    st.caption(words[:350])
    st.download_button('Download '+name,data,file_name=name,mime='video/mp4',key=name)
