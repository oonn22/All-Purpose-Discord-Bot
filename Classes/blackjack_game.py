from random import randint


class BlackjackGame:
    card_symbol_dict = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                        8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K'}
    card_name_dict = {1: 'Ace', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five',
                      6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
                      11: 'Jack', 12: 'Queen', 13: 'King'}

    def __init__(self, msg_id: int, chnl_id: int, player_mention, bet: int):
        self.card_deck = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0,
                          10: 0, 11: 0, 12: 0, 13: 0}
        self.msg_id = msg_id
        self.chnl_id = chnl_id
        self.player_mention = player_mention
        self.player_hand = []
        self.dealer_hand = []
        self.bet = bet
        self.player_last_action = 'Started game'
        self.dealer_last_action = ''
        self.dealer_turn = False
        self.deal_cards()

    def deal_cards(self):
        for i in range(4):
            c = randint(1, 13)
            self.card_deck[c] += 1
            if i % 2 == 0:
                self.player_hand.append(c)
            else:
                self.dealer_hand.append(c)

    def draw_player_card(self):
        c = randint(1, 13)
        while self.card_deck[c] == 4:
            c = randint(1, 13)
        self.player_hand.append(c)
        self.player_last_action = 'Drew a ' + BlackjackGame.card_name_dict[c]

        if BlackjackGame._hand_total(self.player_hand) > 21:
            self.dealer_turn = True
            self.player_last_action += ', went bust'

    def _draw_dealer_card(self):
        c = randint(1, 13)
        while self.card_deck[c] == 4:
            c = randint(1, 13)
        self.dealer_hand.append(c)
        self.dealer_last_action = 'Drew a ' + BlackjackGame.card_name_dict[c]

        if BlackjackGame._hand_total(self.dealer_hand) > 21:
            self.dealer_last_action += ', went bust'

    def print_game(self) -> str:
        game = self.player_mention + '\'s Hand: \n'
        game += self._print_hand(self.player_hand)
        game += '\nLast Action: ' + self.player_last_action
        game += '\n\nDealer\'s Hand: \n'
        game += self._print_hand(self.dealer_hand, is_dealer=True)
        game += '\nLast Action: ' + self.dealer_last_action
        return game

    def _print_hand(self, hand: list, is_dealer=False) -> str:
        s = ''
        i = 0
        for card in hand:
            if not self.dealer_turn and i >= 1 and is_dealer:
                s += '*****  '
            else:
                s += '**' + BlackjackGame.card_symbol_dict[card] + '**  '
            i += 1
        s += '\nTotal: '
        if not is_dealer or self.dealer_turn:
            s += str(BlackjackGame._hand_total(hand))
        return s

    def take_dealer_turn(self) -> list:
        self.dealer_turn = True
        steps = []
        while True:
            if self.dealer_last_action == '':
                self.dealer_last_action = 'Revealed hand'
                steps.append(self.print_game())
            else:
                if BlackjackGame._hand_total(self.dealer_hand) <= 16:
                    self._draw_dealer_card()
                    steps.append(self.print_game())
                else:
                    self.dealer_last_action = 'stand'
                    steps.append(self.print_game())
                    break

                if BlackjackGame._hand_total(self.dealer_hand) > 21:
                    break
        return steps

    def determine_game(self) -> int:
        player_total = self._hand_total(self.player_hand)
        dealer_total = self._hand_total(self.dealer_hand)

        if dealer_total == player_total:
            return 0
        elif dealer_total > 21 and player_total > 21:
            return 0
        elif dealer_total > 21 and player_total <= 21:
            return self.bet * 2
        elif player_total > 21:
            return -1 * self.bet
        elif player_total > dealer_total:
            return self.bet * 2
        else:
            return -1 * self.bet


    @staticmethod
    def _hand_total(hand: list) -> int:
        h = sorted(hand, reverse=True)
        total = 0
        for card in h:
            if card == 1:
                if total + 11 > 21:
                    total += 1
                elif hand.count(1) == 1:
                    total += 11
                else:
                    total += 1
            elif card > 10:
                total += 10
            else:
                total += card
        return total
