"""Default: discovery only. --stream-seconds explicitly probes the operator's gaze."""
import argparse,json,platform,struct,time,threading
from pathlib import Path
from .devices import TobiiDevice
from .quality import valid_point

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stream-seconds',type=float,default=0);parser.add_argument('--report')
 args=parser.parse_args();parser.error('stream seconds must be between 0 and 30') if not 0<=args.stream_seconds<=30 else None
 device=TobiiDevice();status=device.status()
 result={'python':platform.python_version(),'architecture_bits':struct.calcsize('P')*8,'device':status,'recording_started':False,
         'hardware_validation_complete':False,'purpose':'operator diagnostic only, not participant research data'}
 if args.stream_seconds and status['connected']:
  samples=[];lock=threading.Lock()
  def callback(sample):
   with lock:samples.append(sample)
  try:
   result['clock_before']=device.clock_sample();device.start(callback);result['recording_started']=True;time.sleep(args.stream_seconds)
  except Exception as error:result['error']=str(error)
  finally:device.stop()
  result['clock_after']=device.clock_sample();result['sample_count']=len(samples)
  result['valid_fraction']={eye:sum(valid_point(s,eye) for s in samples)/len(samples) if samples else 0 for eye in ('left','right')}
  times=[s['system_time_stamp'] for s in samples]
  result['observed_hz']=(len(times)-1)*1e6/(times[-1]-times[0]) if len(times)>1 and times[-1]>times[0] else None
 if args.report:
  path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
 return 0 if not args.stream_seconds or (status['connected'] and result.get('sample_count',0)>0) else 2
if __name__=='__main__':raise SystemExit(main())
