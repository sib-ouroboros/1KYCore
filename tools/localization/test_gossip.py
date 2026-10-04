import unittest
from sql_dump import Table
from gossip import analyse_gossip
def table(row,key):return Table(list(row),list(key),'',{tuple(row[k] for k in key):row})
class Gossip(unittest.TestCase):
    def fixture(self):
        t={'gossip_menu_option':table({'MenuId':'1','OptionIndex':'0','OptionIcon':'5','OptionText':'Ready.','OptionType':'1','OptionNpcFlag':'1','OptionBroadcastTextId':'0','VerifiedBuild':'0'},('MenuId','OptionIndex')),
           'gossip_menu_option_locale':Table(['MenuId','OptionIndex','Locale','OptionText','BoxText'],['MenuId','OptionIndex'],'',{},limits={'OptionText':('bytes',65535),'BoxText':('bytes',65535)},defaults={'OptionText':'','BoxText':''}),
           'gossip_menu_option_action':Table(['MenuId','OptionIndex','ActionMenuId','ActionPoiId'],['MenuId','OptionIndex'],'',{}),
           'gossip_menu_option_box':table({'MenuId':'1','OptionIndex':'0','BoxCoded':'0','BoxMoney':'0','BoxText':'Confirm.','BoxBroadcastTextId':'0'},('MenuId','OptionIndex')),
           'creature_template':table({'entry':'42','gossip_menu_id':'1','name':'Keeper'},('entry',))}
        s={'gossip_menu_option':table({'MenuID':'1','OptionIndex':'0','OptionNPC':'5','OptionText':'Ready.','OptionType':'1','OptionNpcflag':'1','OptionNpcflag2':'0','OptionBroadcastTextID':'0','BoxBroadcastTextID':'0','BoxCurrency':'0','BoxCoded':'0','BoxMoney':'0','BoxText':'Confirm.','ActionMenuID':'0','ActionPoiID':'0'},('MenuID','OptionIndex')),
           'gossip_menu_option_locale':table({'MenuID':'1','ID':'0','Locale':'ruRU','OptionText':'Готов.','BoxText':'Подтвердить.'},('MenuID','ID','Locale')),
           'creature_template':table({'entry':'42','gossip_menu_id':'1'},('entry',)),
           'creature_template_wdb':table({'Entry':'42','Name1':'Keeper'},('Entry',))}
        return t,s
    def test_owner_icon_action_box_and_grouping(self):
        t,s=self.fixture();r,c,_=analyse_gossip(t,s,'sha')
        self.assertEqual([x['field'] for x in c],['OptionText','BoxText'])
        self.assertEqual(c[0]['key'],c[1]['key'])
        self.assertTrue(any(g.get('absent') for g in c[0]['guards']))
        s['gossip_menu_option'].rows[('1','0')]['ActionMenuID']='2'
        self.assertFalse(analyse_gossip(t,s,'sha')[1])
    def test_foreign_locale_and_missing_owner_preserved(self):
        t,s=self.fixture();t['gossip_menu_option_locale'].rows[('1','0')]={'MenuId':'1','OptionIndex':'0','Locale':'frFR','OptionText':'Pret.','BoxText':''}
        self.assertFalse(analyse_gossip(t,s,'sha')[1])
        t['gossip_menu_option_locale'].rows.clear();s['creature_template'].rows[('42',)]['gossip_menu_id']='2'
        self.assertFalse(analyse_gossip(t,s,'sha')[1])
    def test_broadcast_priority_and_confirmation_identity(self):
        t,s=self.fixture();t['gossip_menu_option'].rows[('1','0')]['OptionBroadcastTextId']='99'
        self.assertEqual([c['field'] for c in analyse_gossip(t,s,'sha')[1]],['BoxText'])
        t['gossip_menu_option_box'].rows[('1','0')]['BoxMoney']='100'
        self.assertFalse(analyse_gossip(t,s,'sha')[1])
if __name__=='__main__':unittest.main()
