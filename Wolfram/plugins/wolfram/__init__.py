__author__ = 'Gareth Coles'

import wolframalpha

from system.command_manager import CommandManager
from system.decorators.threads import run_async_threadpool

import system.plugin as plugin

from system.protocols.generic.channel import Channel
from system.storage.formats import YAML
from system.storage.manager import StorageManager


class WolframPlugin(plugin.PluginObject):

    app = None

    config = None
    commands = None
    storage = None

    def setup(self):
        self.logger.trace("Entered setup method.")
        self.storage = StorageManager()
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/wolfram.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/wolfram.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.commands = CommandManager()

        self._load()
        self.config.add_callback(self._load)

        self.commands.register_command("wolfram", self.wolfram_command, self,
                                       "wolfram.wolfram", default=True)

    def _load(self):
        self.app = wolframalpha.Client(self.config["app_id"])

    @run_async_threadpool
    def wolfram_command(self, protocol, caller, source, command, raw_args,
                        parsed_args):
        target = caller
        if isinstance(source, Channel):
            target = source

        if len(raw_args):
            try:
                res = self.app.query(raw_args)
                first = next(res.results)
                text = first.text.replace("\n", " ")

                target.respond(text)
            except Exception as e:
                if len(str(e)):
                    raise e
                else:
                    target.respond("No answer was found for your query.")

        else:
            caller.respond("Usage: .wolfram <query>")

    def deactivate(self):
        pass
