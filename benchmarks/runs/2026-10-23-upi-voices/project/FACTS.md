# How UPI Payments Work — facts

Labels: [SOURCE] stated by the cited reference; [EXTERNAL] aside.
Sources: W = https://en.wikipedia.org/wiki/Unified_Payments_Interface
S = web search results (NPCI-mapper/switch explainers), e.g. https://m2pfintech.com/blog/npci-mapper-switch-and-psp-decoding-the-upi-transaction-journey/ , https://aswinmohan.me/how-upi-works . These are vendor/blog explainers, not NPCI documentation; the NPCI product page returned no content.

## UPI
- [SOURCE] UPI is an Indian instant payment system developed by NPCI, regulated by the RBI — W
- [SOURCE] Pilot launched 11 April 2016 with 21 member banks — W
- [SOURCE] Users pay with a Virtual Payment Address (UPI ID) tied to a bank account; also QR codes — W
- [SOURCE] A four- or six-digit UPI PIN — W
- [SOURCE] Model has a front-end payment service provider (the app) and a back-end bank on each side — W
- [SOURCE] Transfers move between two bank accounts; any UPI app can be used (Google Pay, PhonePe, Paytm are examples) — W
- [SOURCE] August 2025: about 20 billion transactions worth ₹25 trillion — W

## Flow
- [SOURCE] The app passes the request to NPCI, which resolves the payee's VPA to a bank and sends the request to the payer's bank — S
- [SOURCE] The payer's bank checks the PIN and balance, then debits — S
- [SOURCE] The payee's bank credits and returns success via NPCI to both apps; typically within seconds — S
