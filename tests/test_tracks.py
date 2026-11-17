import json
from pathlib import Path

def test_track_registry_is_explicitly_unavailable_until_verified():
    registry=json.loads((Path(__file__).parents[1]/'config/tracks.json').read_text(encoding='utf-8'))
    tracks=registry['tracks']
    assert len(tracks)==30 and len({t['track_id'] for t in tracks})==30
    for group in 'ABC':assert sum(t['group']==group for t in tracks)==10
    assert [tracks[i]['copy_of'] for i in [9,19,29]]==['T01','T11','T21']
    for t in tracks:
        assert not t['ready'] and t['missing']
        assert [r['family'] for r in t['rounds']]==registry['round_order']
        assert [r['test_index'] for r in t['rounds']]==[0,1,2,3]
        assert t['mapping_complete']
        assert all(not r['verified'] and r['mapping_verified'] and r['variant_id'] for r in t['rounds'])

    assert tracks[0]['rounds'][1]['variant_label']=='Search(Good)+Status(Bad)'
    assert tracks[15]['rounds'][2]['variant_label']=='Button(Good)+Search(Good)'
    assert tracks[27]['rounds'][2]['variant_label']=='Status(Good)+Search(Good)'
    for duplicate,original in [(9,0),(19,10),(29,20)]:
        assert tracks[duplicate]['rounds']==tracks[original]['rounds']
        assert tracks[duplicate]['track_id']!=tracks[original]['track_id']
    assert len({r['variant_id'] for t in tracks for r in t['rounds']})==19
