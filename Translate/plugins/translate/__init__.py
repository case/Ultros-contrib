__author__ = 'Gareth Coles'

from goslate import Goslate, Error

from kitchen.text.converters import to_unicode

from system.decorators.threads import run_async_threadpool
from system.command_manager import CommandManager
from system.plugins.plugin import PluginObject


class TranslatePlugin(PluginObject):
    commands = None
    goslate = None

    def setup(self):
        self.commands = CommandManager()
        self.goslate = Goslate()

        self.commands.register_command(
            "translate", self.translate_command, self, "translate.translate",
            ["tr", "t"], True
        )

    @run_async_threadpool
    def translate_command(self, protocol, caller, source, command, raw_args,
                          parsed_args):
        if len(parsed_args) < 2:
            caller.respond(
                "Usage: {CHARS}" + command + " <languages> <text>"
            )
            return

        langs = parsed_args[0]
        text = u" ".join([to_unicode(x) for x in parsed_args[1:]])

        if u":" in langs:
            split = langs.split(u":")
            from_lang, to_lang = split[0], split[1]
        else:
            from_lang, to_lang = u"", langs

        try:
            translation = self.goslate.translate(text, to_lang, from_lang)

            source.respond(u"[{}] {}".format(to_lang, translation))
        except Error as e:
            source.respond(u"Translation error: {}".format(e))
        except Exception as e:
            self.logger.exception("Translation error")
            source.respond(u"Translation error: {}".format(e))
