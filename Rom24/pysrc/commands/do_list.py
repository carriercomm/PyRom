from collections import OrderedDict
import merc
import interp

def do_list(self, argument):
    if merc.IS_SET(ch.in_room.room_flags, merc.ROOM_PET_SHOP):
        # hack to make new thalos pets work */
        pRoomIndexNext = None
        if ch.in_room.vnum == 9621:
            if 9706 in merc.room_index_hash:
                pRoomIndexNext = merc.room_index_hash[9706]
        else:
            if ch.in_room.vnum+1 in merc.room_index_hash:
                pRoomIndexNext = merc.room_index_hash[ch.in_room.vnum+1]
        if not pRoomIndexNext:
            print("BUG: Do_list: bad pet shop at vnum %d." % ch.in_room.vnum)
            ch.send("You can't do that here.\n")
            return
        found = False
        for pet in pRoomIndexNext.people:
            if merc.IS_SET(pet.act, merc.ACT_PET):
                if not found:
                    found = True
                    ch.send("Pets for sale:\n")
                ch.send("[%2d] %8d - %s\n" % (pet.level, 10 * pet.level * pet.level, pet.short_descr))
        if not found:
            ch.send("Sorry, we're out of pets right now.\n")
        return
    else:
        keeper = merc.find_keeper(ch)
        if not keeper:
            return
        argument, arg = merc.read_word(argument)
        items = OrderedDict()
        for obj in keeper.carrying:
            cost = merc.get_cost(keeper, obj, True)
            if obj.wear_loc == merc.WEAR_NONE and ch.can_see_obj(obj) and cost > 0 \
            and ( not arg or arg in obj.name.lower()):
                if merc.IS_OBJ_STAT(obj, merc.ITEM_INVENTORY):
                    items[(obj.pIndexData, obj.short_descr)] = (obj, -1)
                else:
                    k = (obj.pIndexData, obj.short_descr)
                    if k not in items:
                        items[k] = (obj, 1)
                    else:
                        items[k][1] += 1
        if not items:
            ch.send("You can't buy anything here.\n")
            return
        ch.send("[Lv Price Qty] Item\n")
        for k, p in items.items():
            obj, count = p
            cost = merc.get_cost(keeper, obj, True)
            ch.send("[%2d %5d %2s ] %s" % (obj.level,cost, ("--" if count == -1 else count),obj.short_descr))
            if merc.IS_SET(ch.act, merc.PLR_OMNI):
                ch.send("(%d)" % obj.pIndexData.vnum)
            ch.send("\n")

interp.cmd_table['list'] = interp.cmd_type('list', do_list, merc.POS_RESTING, 0, merc.LOG_NORMAL, 1)