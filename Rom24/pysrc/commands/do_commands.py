import merc
import interp


def do_commands(ch, argument):
    col = 0
    for key, cmd in interp.cmd_table.items():
        if cmd.level <  merc.LEVEL_HERO and cmd.level <= ch.get_trust() and cmd.show:
            ch.send("%-12s" % key)
            col += 1
            if col % 6 == 0:
                ch.send("\n")
    if col % 6 != 0:
        ch.send("\n")
    return

interp.cmd_table['commands'] = interp.cmd_type('commands', do_commands, merc.POS_DEAD, 0, merc.LOG_NORMAL, 1)