# coding=utf-8

"""
wow.py:
Written by Zarthus <zarthus@zarth.us> May 30, 2014.
Gets data from the World of Warcraft Armoury API

Commands:
armoury, armory: Request data from the armoury API and format it into something
human readable.
"""

import re
import requests

import system.plugin as plugin
from system.command_manager import CommandManager
from system.decorators.threads import run_async_threadpool


class WoWPlugin(plugin.PluginObject):
    commands = None

    def setup(self):
        self.commands = CommandManager()

        self.commands.register_command('armoury', self.armoury,
                                       self, 'wow.armoury',
                                       aliases=['armory'], default=True)

    @run_async_threadpool
    def armoury(self, protocol, caller, source, command, raw_args,
                parsed_args):
        """
        armoury [realm] [character name] [region = EU]
        Look up character and returns API data.
        """

        if parsed_args is None:
            parsed_args = raw_args.split()

        # Splits input, builds the API url, and returns the formatted data to
        # user.

        if len(parsed_args) < 2:
            return caller.respond('{CHARS}armoury [realm] [character name] '
                                  '[region = EU] - Look up character and '
                                  'returns API data.')

        realm = parsed_args[0].replace('_', '-').lower()
        charname = parsed_args[1].lower()

        # Sets the default region to EU if none specified.
        if len(parsed_args) < 3:
            region = 'eu'
        else:
            region = parsed_args[2].lower()

        if not re.match(r'^[a-z]{1,3}$', region):
            return caller.respond('The region specified is not a valid '
                                  'region. Valid regions: eu, us, sea, kr, '
                                  'tw.')

        if re.match(r'^[^\d]$', charname) or len(charname) > 18:
            # May not contain digits, repeat the same letter three times,
            # or contain non-word characters.
            # Special characters are permitted, such as ������.
            return caller.respond('The character name is not a valid name.'
                                  'Character names can only contain letters, '
                                  'special characters, and be 18 characters '
                                  'long.')

        if not re.match(r'^[a-z\' _-]{3,32}$', realm):
            # Realm names can have spaces in them, use dashes for this.
            return caller.respond('The realm name is not a valid name. '
                                  'Realm names can only contain letters, '
                                  'dashes, and apostrophes, up to 32 '
                                  'characters')

        region_short = self.wow_region_shortname(region)

        if not region_short:
            return caller.respond(
                'The region \'{}\' does not exist.'.format(region)
            )

        link = 'http://{0}.battle.net/api/wow/character/{1}/{2}'.format(
            region, realm, charname
        )

        source.respond(self.wow_armoury_data(link))

    def wow_armoury_data(self, link):
        """
        Sends the API request, and returns the data accordingly
        (in json if raw, nicely formatted if not).
        """
        try:
            data = requests.get(link)
        except Exception as e:
            return 'Unable to fetch information for {}. ' + \
                'Does the realm or character exist? ({})'.format(link, str(e))

        return self.wow_armoury_format(data, link)

    def wow_armoury_format(self, data, link):
        """Format armoury data into a human readable string"""

        if data.status_code != 200 and data.status_code != 404:
            # The page returns 404 if the character or realm is not found.
            try:
                data.raise_for_status()
            except Exception as e:
                return (
                    'An error occurred while trying to fetch the data. '
                    '({})'.format(
                        str(e)
                    ))

        data = data.json()

        if len(data) == 0:
            return 'Could not find any results.'

        if 'reason' in data:
            # Something went wrong
            # (i.e. realm does not exist, character does not exist).
            return data['reason']

        if 'name' in data:
            niceurl = link.replace('/api/wow/', '/wow/en/') + '/simple'

            try:
                return (
                    '{0} is a level \x0307{1}\x0F {2} {3} on {4} with \x0307'
                    '{5}\x0F achievement points and \x0307{6}\x0F honourable '
                    'kills. Armoury Profile: {7}'.format(
                        data['name'], data['level'],
                        self.wow_get_gender(data['gender']),
                        self.wow_get_class(data['class'], True),
                        data['realm'],
                        data['achievementPoints'],
                        data['totalHonorableKills'],
                        niceurl
                    ))
            except Exception as e:
                return (
                    'Unable to fetch information for {}. Does the realm or '
                    'character exist? ({})'.format(
                        niceurl,
                        str(e)
                    ))

        return 'An unexpected error occured.'

    def wow_get_gender(self, genderid):
        """Formats a gender ID to a readable gender name"""
        gender = 'unknown'

        if genderid == 0:
            gender = 'male'
        elif genderid == 1:
            gender = 'female'

        return gender

    def wow_get_class(self, classid, colours=False):
        """
        Formats a class ID to a readable name
        Data from http://eu.battle.net/api/wow/data/character/classes
        """
        if colours:
            # Format their colours according to class colours.
            classids = {
                1: '\x0305Warrior\x0F', 2: '\x0313Paladin\x0F',
                3: '\x0303Hunter\x0F', 4: '\x0308Rogue\x0F',
                5: 'Priest', 6: '\x0304Death Knight\x0F',
                7: '\x0310Shaman\x0F', 8: '\x0311Mage\x0F',
                9: '\x0306Warlock\x0F', 10: '\x0309Monk\x0F',
                11: '\x0307Druid\x0F'
            }
        else:
            classids = {
                1: 'Warrior', 2: 'Paladin', 3: 'Hunter', 4: 'Rogue',
                5: 'Priest', 6: 'Death Knight', 7: 'Shaman', 8: 'Mage',
                9: 'Warlock', 10: 'Monk', 11: 'Druid'
            }

        if classid in classids:
            return classids[classid]
        else:
            return 'unknown'

    def wow_get_race(self, raceid):
        """
        Formats a race ID to a readable race name
        Data from http://eu.battle.net/api/wow/data/character/races
        """
        raceids = {
            1: 'Human', 2: 'Orc', 3: 'Dwarf', 4: 'Night Elf', 5: 'Undead',
            6: 'Tauren', 7: 'Gnome', 8: 'Troll', 9: 'Goblin', 10: 'Blood Elf',
            11: 'Draenei', 22: 'Worgen', 24: 'Pandaren (neutral)',
            25: 'Pandaren (alliance)', 26: 'Pandaren (horde)'
        }

        if raceid in raceids:
            return raceids[raceid]
        else:
            return 'unknown'

    def wow_region_shortname(self, region):
        """
        Returns a short region name,
        which functions as battle.net their subdomain (i.e. eu.battle.net)
        """
        validregions = {
            'eu': 'eu', 'europe': 'eu',
            'us': 'us',
            'sea': 'sea', 'asia': 'sea',
            'kr': 'kr', 'korea': 'kr',
            'tw': 'tw', 'taiwan': 'tw'
        }

        if region in validregions:
            return validregions[region]
        else:
            return False
