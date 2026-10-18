import unittest
from profiles import validate_config, default_config, packet_for, parse_reply

class ProfilesTest(unittest.TestCase):
    def test_default_exact_receivers(self):
        c=validate_config(default_config())
        self.assertEqual(c['devices'][0]['vid'],'373B')
        self.assertEqual(c['devices'][1]['pid'],'FA09')
    def test_invalid_hex_never_normalized(self):
        for bad in ['373Bz','0x373B','373',' 373B','373B ']:
            c=default_config();c['devices'][0]['vid']=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):validate_config(c)
    def test_unknown_protocol_refused(self):
        c=default_config();c['devices'][0]['protocol']='generic'
        with self.assertRaises(ValueError):validate_config(c)
    def test_cross_role_refused(self):
        c=default_config();c['devices'][0]['protocol']='beiying_keyboard'
        with self.assertRaises(ValueError):validate_config(c)
    def test_poll_bounds_and_boolean(self):
        for bad in [True,0,1,61,3.5]:
            c=default_config();c['poll_seconds']=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):validate_config(c)
    def test_atk_checksum_and_fields(self):
        p=packet_for('compx_mouse');self.assertEqual(len(p),17);self.assertEqual(sum(p)&255,85)
        r=[8,4,0,0,0,2,80,0,15,126,0,0,0,0,0,0,106]
        self.assertEqual(parse_reply('compx_mouse',r),{'percent':80,'charging':False})
        r[-1]^=1;self.assertIsNone(parse_reply('compx_mouse',r))
    def test_keyboard_checksum_and_fields(self):
        p=packet_for('beiying_keyboard');self.assertEqual(p[:3],[19,74,1]);self.assertEqual(len(p),20);self.assertEqual(sum(p[:-1])&255,p[-1])
        r=[19,74,1,0,2,100,17]+[0]*12+[213]
        self.assertEqual(parse_reply('beiying_keyboard',r),{'percent':100,'charging':True})
        r[-1]^=1;self.assertIsNone(parse_reply('beiying_keyboard',r))
    def test_malformed_reports_not_percentages(self):
        for protocol in ['compx_mouse','beiying_keyboard']:
            for r in [[],[0]*20,[255]*20,[8,4,80],list(range(64))]:
                with self.subTest(protocol=protocol,r=r):self.assertIsNone(parse_reply(protocol,r))
    def test_configuration_is_independent_copy(self):
        a=default_config();b=default_config();a['devices'][0]['name']='Changed'
        self.assertNotEqual(a,b)

if __name__=='__main__':unittest.main()
