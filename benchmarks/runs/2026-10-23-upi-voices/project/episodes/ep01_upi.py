from manimvox.kit import *


def parties():
    app = node("Your app", "pay", w=2.2, color=BLUE).move_to([-5.0, 0, 0])
    sw = node("NPCI switch", "routes", w=2.4, color=ACCENT).move_to([-1.6, 0, 0])
    mine = node("Your bank", "debits you", w=2.4, color=ORANGE).move_to([4.2, 1.2, 0])
    shop = node("Shop's bank", "credits shop", w=2.4, color=TEAL).move_to([4.2, -1.2, 0])
    links = [arrow(app, sw), arrow(sw, mine), arrow(sw, shop)]
    return app, sw, mine, shop, links


class Ep01(Episode):
    EP = 1
    TITLE = "How UPI payments work"
    TAGLINE = "One payment, two banks, a few seconds"
    NCHAP = 2

    def build(self):
        ph = icon_phone(BLUE, 1.6).move_to([-2.5, 0, 0])
        shop = icon_shop(TEAL, 1.6).move_to([2.5, 0, 0])
        a = arrow(ph, shop, color=ACCENT, label="₹")
        self.say("You scan a code and type a PIN. A second later, the shop has your money.",
                 FadeIn(ph), FadeIn(shop), Create(a))
        self.intro("How does money cross two banks that fast? By the end, you will follow one payment from your phone to the shop.",
                   question="How does money cross two banks in seconds?")

        self.chapter("Four parties")
        self.say("N P C I, the National Payments Corporation of India, built UPI.")
        self.clear()
        self.add(heading("A payment passes through four parties"))
        app, sw, mine, shopb, links = parties()
        self.steps("There is your app, a central switch run by N P C I, your bank, and the shop's bank.",
                   [FadeIn(app), FadeIn(sw), FadeIn(mine), FadeIn(shopb), [Create(l) for l in links]])
        uid = T("shop@bank", 26, ACCENT, max_w=4).move_to([-3.3, -2.3, 0])
        self.say("You do not need the shop's account number. A UPI ID, like this one, stands in for it.", FadeIn(uid))
        self.beat()

        self.chapter("One payment")
        self.add(heading("One payment, step by step"))
        app, sw, mine, shopb, links = parties()
        self.add(app, sw, mine, shopb, *links)
        s1 = chip("1  amount + PIN", BLUE).next_to(app, DOWN, buff=0.4)
        self.say("You pick the payee, enter the amount, and your PIN. The app sends the request to the switch.",
                 FadeIn(s1), Indicate(links[0][0]))
        s2 = chip("2  asks your bank", ACCENT).next_to(sw, DOWN, buff=0.4)
        self.say("The switch finds the shop's bank from the UPI ID, and asks yours.", FadeIn(s2), Indicate(links[1][0]))
        s3 = chip("3  PIN, balance, debit", ORANGE).next_to(mine, UP, buff=0.3)
        self.say("Your bank checks the PIN and your balance, then takes the money out.", FadeIn(s3))
        s4 = chip("4  credit", TEAL).next_to(shopb, DOWN, buff=0.3)
        self.say("The shop's bank adds it, and a confirmation travels back to both of you.", FadeIn(s4), Indicate(links[2][0]))
        self.beat()

        self.outro([],
                   "One switch joins two banks, so a single request debits you and credits the shop. In August 2025, UPI handled about twenty billion payments.",
                   answer="A central switch links the two banks, so one request moves the money.")
