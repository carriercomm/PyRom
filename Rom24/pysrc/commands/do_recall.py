import logging
import handler_game

logger = logging.getLogger()

import interp
import merc
import random
import fight
import state_checks
import update



def do_recall(ch, argument):
    if ch.is_npc() and not ch.act.is_set(merc.ACT_PET):
        ch.send("Only players can recall.\n")
        return
    handler_game.act("$n prays for transportation!", ch, 0, 0, merc.TO_ROOM)
    location = merc.roomTemplate[merc.ROOM_VNUM_TEMPLE]
    if not location:
        ch.send("You are completely lost.\n")
        return
    if ch.in_room == location:
        return
    if state_checks.IS_SET(ch.in_room.room_flags, merc.ROOM_NO_RECALL) or ch.is_affected(merc.AFF_CURSE):
        ch.send("Mota has forsaken you.\n")
        return
    victim = ch.fighting
    if victim:
        skill = ch.get_skill("recall")
        if random.randint(1, 99) < 80 * skill / 100:
            ch.check_improve( "recall", False, 6)
            state_checks.WAIT_STATE(ch, 4)
            ch.send("You failed!.\n")
            return
        lose = 25 if ch.desc else 50
        update.gain_exp(ch, 0 - lose)
        ch.check_improve( "recall", True, 4)
        ch.send("You recall from combat!  You lose %d exps.\n" % lose)
        fight.stop_fighting(ch, True)
    ch.move /= 2
    handler_game.act("$n disappears.", ch, None, None, merc.TO_ROOM)
    ch.from_environment()
    ch.to_environment(location)
    handler_game.act("$n appears in the room.", ch, None, None, merc.TO_ROOM)
    ch.do_look("auto")

    if ch.pet is not None:
        ch.pet.do_recall("")
    return


interp.register_command(interp.cmd_type("recall", do_recall, merc.POS_FIGHTING, 0, merc.LOG_NORMAL, 1))
interp.register_command(interp.cmd_type("/", do_recall, merc.POS_FIGHTING, 0, merc.LOG_NORMAL, 0))
