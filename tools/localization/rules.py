"""Explicit semantic mappings; names and columns are never guessed by position."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    category: str
    target: str
    source: str
    base_target: str
    base_source: str
    keys_target: tuple
    keys_source: tuple
    base_keys_target: tuple
    base_keys_source: tuple
    fields: tuple  # target locale, source locale, target English, source English
    identity: tuple = ()  # target base/source base semantic fields
    locale: str = 'locale'  # None for an existing wide server-string row.
    mode: str = 'game'


QUEST_FIELDS=tuple((name,name,name,name) for name in ('LogTitle','LogDescription','QuestDescription','AreaDescription','PortraitGiverText','PortraitGiverName','PortraitTurnInText','PortraitTurnInName','QuestCompletionLog'))
RULES=(
    Rule('quests','quest_template_locale','quest_template_locale','quest_template','quest_template',('ID',),('ID',),('ID',),('ID',),QUEST_FIELDS,(('LogTitle','LogTitle'),('QuestType','QuestType'),('QuestSortID','QuestSortID'))),
    Rule('rewards','quest_offer_reward_locale','quest_offer_reward_locale','quest_offer_reward','quest_offer_reward',('ID',),('ID',),('ID',),('ID',),(('RewardText','OfferRewardText','RewardText','RewardText'),)),
    Rule('requests','quest_request_items_locale','quest_request_items_locale','quest_request_items','quest_request_items',('ID',),('ID',),('ID',),('ID',),(('CompletionText','CompletionText','CompletionText','CompletionText'),)),
    Rule('objectives','quest_objectives_locale','quest_objectives_locale','quest_objectives','quest_objectives',('ID',),('ID',),('ID',),('ID',),(('Description','Description','Description','Description'),),(('QuestID','QuestID'),('Type','Type'),('ObjectID','ObjectID'),('Amount','Amount'),('StorageIndex','StorageIndex'))),
    Rule('pages','page_text_locale','page_text_locale','page_text','page_text',('ID',),('ID',),('ID',),('ID',),(('Text','Text','Text','Text'),),(('NextPageID','NextPageID'),)),
    Rule('npcs','creature_template_locale','creature_template_wdb_locale','creature_template','creature_template_wdb',('entry',),('ID',),('entry',),('Entry',),(('Name','Name1','name','Name1'),('NameAlt','NameAlt1','femaleName','NameAlt1'),('Title','Title','subname','Title'),('TitleAlt','TitleAlt','TitleAlt','TitleAlt')),(('name','Name1'),('type','Type'),('family','Family'))),
    Rule('objects','gameobject_template_locale','locales_gameobject','gameobject_template','gameobject_template',('entry',),('entry',),('entry',),('entry',),(('name','name_loc8','name','name'),('castBarCaption','castbarcaption_loc8','castBarCaption','castBarCaption')),(('name','name'),('type','type'))),
    Rule('choices','playerchoice_locale','playerchoice_locale','playerchoice','playerchoice',('ChoiceId',),('ChoiceId',),('ChoiceId',),('ChoiceId',),(('Question','Question','Question','Question'),)),
    Rule('responses','playerchoice_response_locale','playerchoice_response_locale','playerchoice_response','playerchoice_response',('ChoiceId','ResponseId'),('ChoiceId','ResponseId'),('ChoiceId','ResponseId'),('ChoiceId','ResponseId'),tuple((f,f,f,f) for f in ('Header','Answer','Description','Confirmation')),(('Index','Index'),)),
    Rule('server_strings','trinity_string','trinity_string','trinity_string','trinity_string',('entry',),('entry',),('entry',),('entry',),(('content_loc8','content_loc8','content_default','content_default'),),locale=None,mode='printf'),
)

HOTFIX_RULES=(Rule('broadcast','broadcast_text_locale','broadcast_text_locale','broadcast_text','broadcast_text',('ID',),('ID',),('ID',),('ID',),(('Text_lang','Text_lang','Text','Text'),('Text1_lang','Text1_lang','Text1','Text1')),(('Text','Text'),('Text1','Text1'))),)

POI_RULES=(Rule('pointers','points_of_interest_locale','locales_points_of_interest','points_of_interest','points_of_interest',('ID',),('entry',),('ID',),('entry',),(('Name','icon_name_loc8','Name','icon_name'),),(('PositionX','x'),('PositionY','y'),('Icon','icon'),('Flags','flags'),('Importance','data'))),)


def selected_tables(rules=RULES):
    extra={'gossip_menu_option','gossip_menu_option_locale','gossip_menu_option_action','gossip_menu_option_box','creature_text','creature_text_locale','trinity_string'} if rules==RULES else set()
    return {table for rule in rules for table in (rule.target,rule.source,rule.base_target,rule.base_source)} | extra


def projection(rules=RULES):
    result={}
    # Keep full locale rows for exact inserted-row rollback; project only wide bases.
    locale={rule.target for rule in rules}|{rule.source for rule in rules}
    for rule in rules:
        for table,keys,fields in ((rule.base_target,rule.base_keys_target,[f[2] for f in rule.fields]+[f[0] for f in rule.identity]),(rule.base_source,rule.base_keys_source,[f[3] for f in rule.fields]+[f[1] for f in rule.identity])):
            if table not in locale:result.setdefault(table,set()).update(keys+tuple(fields))
    for table in ('quest_template',):
        result.setdefault(table,set()).update(('ID','QuestType','QuestSortID','LogTitle','Expansion'))
    if rules==RULES:
        result.setdefault('creature_template',set()).update(('entry','gossip_menu_id'))
    return result
