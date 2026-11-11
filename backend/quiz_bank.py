"""Additional hand-authored questions for the numbered lessons.

Each row names the skill and gives a prompt, the correct answer, two
distractors, and feedback. IDs use the skill name and stay stable when
questions are reordered.
"""

BANK = {
    0: """
CAN arbitration|Ce se întâmplă când două noduri încearcă să trimită simultan cadre CAN cu ID-uri standard diferite?|Arbitrajul păstrează cadrul cu prioritate mai mare|Ambele cadre sunt acceptate simultan|Nodurile aleg la întâmplare un câștigător|În arbitrajul dintre aceste cadre, ID-ul numeric mai mic are prioritate.
CAN destination|Un ID CAN standard identifică direct destinatarul cadrului?|Nu, identifică mesajul și contribuie la prioritate|Da, ID-ul este adresa nodului destinatar|Da, cu excepția mesajelor fără date|Nodurile pot recepționa și filtra cadrele după identificator.
Classical CAN length|Câți octeți de date poate conține cel mult un cadru de date CAN clasic?|8|16|64|CAN clasic permite până la 8 octeți în payload.
Trace window|Unde cauți ID-ul, direcția, datele și timestamp-ul unui cadru în CANoe?|Trace Window|Write Window|Editorul CAPL|Trace afișează evenimentele de comunicație și câmpurile cadrelor.
Graphics window|Ce fereastră este potrivită pentru a urmări evoluția vitezei decodate în timp?|Graphics Window|Write Window|Simulation Setup|Graphics afișează evoluția semnalelor ca serii în timp.
Simulation setup|Unde configurezi nodurile simulate în CANoe?|Simulation Setup|Trace Window|Graphics Window|Simulation Setup definește nodurile care participă la simulare.
Events|Ce declanșează codul din on message pentru un ID ales?|Recepția unui cadru cu ID-ul urmărit|Orice click în editor|Pornirea fiecărui timer|Handlerul de recepție răspunde evenimentului CAN corespunzător.
Console versus bus|Un log din write() dovedește că un cadru a apărut în Trace?|Nu, verifici separat transmisia|Da, orice log produce un cadru|Da, dacă logul conține ID-ul|Mesajele text și traficul CAN sunt două tipuri de evidență.
Raw versus physical|Ce două câmpuri convertesc valoarea raw într-o valoare fizică după extragerea semnalului?|Factorul și offset-ul|ID-ul și DLC-ul|Timestamp-ul și direcția|Conversia este raw × factor + offset.
Endianness|În reprezentarea little-endian a unui câmp pe doi octeți, unde este octetul mai puțin semnificativ?|Primul|Al doilea|În afara payload-ului|Little-endian pune octetul cu pondere mai mică primul.
Signal definition|De ce este util un fișier DBC când analizezi un payload?|Descrie cum se extrag și se interpretează semnalele|Schimbă fizic octeții deja capturați|Înlocuiește timestamp-urile cadrelor|DBC definește poziția, lungimea, ordinea și conversia semnalelor.
CAPL timer|Ce reprezintă valoarea 500 din setTimer pentru un msTimer?|Întârzierea de 500 ms până la expirare|ID-ul unui cadru|Numărul de cadre care vor fi transmise|msTimer folosește milisecunde.
Test stimulus|Într-un test în care trimiți o comandă ACC, ce este stimulul?|Comanda trimisă către sistem|Verdictul final|Captura de ecran a raportului|Stimulul este acțiunea prin care declanșezi comportamentul urmărit.
Test evidence|Ce compari pentru a decide dacă răspunsul s-a încadrat în termen?|Timpul măsurat de la stimul până la răspuns și termenul cerut|DLC-ul și factorul semnalului|Ordinea taburilor|Comparația trebuie raportată la momentul stimulului.
Missing setup|De ce verifici precondițiile înainte de stimul?|Ca verdictul să reflecte comportamentul în condițiile cerute|Ca să elimini nevoia de a observa răspunsul|Ca orice răspuns să fie considerat corect|Precondițiile definesc situația în care cerința se aplică.
Application CRC|Ce poate detecta un CRC la nivelul aplicației?|O modificare a datelor pe care le protejează|Lipsa tuturor mesajelor viitoare|O tranziție ACC prea lentă în toate cazurile|Verificarea CRC compară valoarea primită cu cea calculată din câmpurile protejate.
Sequence counter|Ce mecanism te ajută să detectezi un mesaj repetat în secvența E2E?|Compararea contorului cu ultimul contor acceptat|Verificarea doar a unității din DBC|Mărirea timeout-ului|Contorul adaugă informație despre ordinea mesajelor.
CRC layers|CRC-ul CAN și CRC-ul E2E al aplicației sunt același câmp?|Nu, operează la niveluri diferite|Da, sunt același octet al payload-ului|Da, au mereu aceleași date de intrare|CRC-ul de legătură protejează cadrul CAN, iar CRC-ul E2E protejează date definite de aplicație.
ACC meaning|Ce funcție descrie ACC?|Controlul adaptiv al vitezei de croazieră|Frânarea automată de urgență|Decodarea unei baze DBC|ACC vine de la Adaptive Cruise Control.
AEB meaning|Ce funcție descrie AEB?|Frânarea automată de urgență|Controlul adaptiv al vitezei de croazieră|Arbitrajul magistralei CAN|AEB vine de la Automatic Emergency Braking.
TTC definition|Ce estimează TTC într-un scenariu simplificat cu apropiere continuă?|Timpul până la coliziune dacă mișcarea se menține|Distanța parcursă în ultima secundă|Timpul necesar pentru a transmite cadrul CAN|TTC înseamnă Time to Collision.
No braking expected|De ce testezi și situații în care AEB nu ar trebui să intervină?|Ca să detectezi frânări nejustificate|Ca să eviți testarea senzorilor|Ca să forțezi o intervenție în toate cazurile|Un test negativ verifică absența intervenției când cerința nu o solicită.
Debug order|Un ECU nu răspunde. Ce verifici mai întâi în trasă înainte de a interpreta verdictul?|Dacă stimulul a fost transmis când era așteptat|Dacă scorul quizului a fost salvat|Dacă primul cadru are DLC maxim|Fără stimulul corect, lipsa unui răspuns nu dovedește singură o defecțiune a ECU.
Trace context|De ce salvezi timestamp-urile împreună cu stările semnalelor?|Ca să poți reconstrui ordinea și întârzierile evenimentelor|Ca să schimbi unitatea de viteză|Ca să nu mai fie nevoie de cerință|Timestamp-urile arată când s-au produs stimulii și răspunsurile.
""",
    1: """
Measurement startup|Which action runs the on start handler in this lab?|Starting a measurement|Opening the Theory tab|Editing the program|Starting the measurement dispatches on start.
Independent runs|Run the same one-log startup program twice. What remains in Console after the second run?|The log from the second run|Both runs' logs|Only the first run's log|Each run starts a new measurement and displays its own output.
Exact log text|The task expects ECU ready. Your startup log is ECU ready!. What should you change?|Remove the exclamation mark|Add another write call|Change the CAN identifier|The exercise compares the exact log text.
Empty startup|A program defines only an on key handler. What happens to that handler during startup?|It waits for its matching key|It runs once at startup|It runs on every clock tick|Keyboard events and startup are dispatched separately.
Source editing|You edited the CAPL code but still see no new output. What action runs the edit?|Click Run|Switch to Progress|Open Reference reading|Editing the source does not execute a handler.
String literals|Which argument is a string literal for write()?|"ECU ready"|ECU ready|0x123|Double quotes delimit the text in this CAPL subset.
Statement termination|Which line correctly ends a CAPL log statement?|write("Ready");|write("Ready"):|write("Ready"),|A semicolon ends the function-call statement.
Handler body|Where should a startup write() call go?|Inside the braces of on start|After the handler's closing brace|Inside a CAN frame ID field|The braces enclose the statements the handler executes.
Run versus check|What does Check exercise do beyond displaying Console output?|Checks the requirement and records completion on success|Configures a physical CAN bus|Automatically changes the program|The checker compares behavior with the exercise and saves a passing result.
Syntax diagnosis|The simulator reports an unterminated string. What should you inspect first?|The opening and closing double quotes|The CAN bit rate|The database password|An unterminated string has no matching closing quote.
Source comments|What happens to a line beginning with // inside a handler?|It is ignored by the interpreter|Its text is logged|It transmits a frame|A line comment is explanatory source text.
CAPL event model|Why is on start called an event handler?|Its body runs in response to a measurement event|Its body repeats continuously|It is an entry in the trace table|A handler is invoked when its corresponding event occurs.
Multiple startup logs|The program prints Ready twice and the task wants it once. What should you look for first?|An extra write() on the executed path|An incorrect DLC|An extra signal factor|Each executed write() adds one line.
Missing handler|A program declares a variable and has no event handler. Why is there no startup log?|Nothing calls write() on startup|All variables are sent to CAN Trace|A keyboard event automatically runs the declaration as a log|A declaration alone does not produce console output.
CANoe measurement|What is the role of the Write window in CANoe?|Display text messages from CAPL|Set the payload of received frames|Display only decoded speed curves|The Write window is for textual diagnostics.
Trace evidence|A log says Frame sent. What separately confirms simulated transmission?|A matching Tx row in CAN Trace|The presence of the word sent|An open editor tab|The Tx row records the actual frame event.
""",
    2: """
Missing output|Expected Boot, Ready. Observed only Boot. What is missing?|A second executed log statement|A larger CAN DLC|A new measurement after every log|The observed sequence lacks its second entry.
Case sensitivity|Expected System ready. Observed system ready. Why can the exercise fail?|The first character differs|The CAN ID differs|Two handlers started|Exact text matching includes capitalization.
Whitespace|Expected System ready. Observed System  ready. What differs?|There is an extra space inside the log text|The order of handlers|The number of CAN bytes|An extra space changes the required string.
Combined lines|Expected two console entries: Boot and Ready. Does one call that logs "Boot Ready" satisfy it?|No, it produces one entry|Yes, it contains both words|Yes, if DLC is two|Entry count matters as well as text.
Local order|Which edit swaps the order of two startup log entries?|Swap their write() statements|Swap their variable names without moving the calls|Click Run twice|Within one handler, the calls execute in source order.
Repeated startup|Why does a second click on Run not append another pair of console lines?|It starts a fresh run|The second write() becomes a CAN frame|Only the first run executes CAPL|The console is replaced with the output of the latest run.
Trace logging mix|A handler calls write(), output(), then write(). How many Tx frames does it submit?|One|Two|Three|Only output() submits a frame.
Declaration placement|Where should two startup log calls go to run in a single ordered sequence?|Together inside on start|One in on start and one in an unrelated key handler|Both in a variables block|One startup handler runs its statements sequentially.
Changing text|Which edit changes the second message without affecting its position?|Edit the second write() argument in place|Move the second call above the first|Remove the first call|Changing a literal leaves call order intact.
Causal check|Why inspect the ordered output rather than search only for Ready?|Ready may be present even when the sequence is wrong|Console output cannot show Ready|Search always checks the preceding entry|Presence alone does not check position or extra output.
Duplicate log diagnosis|Expected Boot then Ready; observed Boot, Boot, Ready. What does the extra Boot indicate?|An additional executed log call or repeated call path|A missing Ready|That the identifier is extended|Each occurrence reflects a separate log action.
Independent evidence|When verifying two ordered logs and two transmitted frames, which evidence do you need?|Console entries and Tx trace rows|Only the last console line|Only the DLC field|Logs and frames are recorded independently.
Consecutive snapshots|You change a byte after the final output() and never call output() again. What appears in Trace?|Only the earlier transmitted payload|An extra frame with the new byte|The earlier frame with its byte replaced|Assignments change the buffer without adding or editing recorded frames.
Log count|A startup handler contains a commented-out write() and two active write() calls. How many entries appear?|Two|Three|One|Only the active calls run.
Requirement order|What is the clearest representation of a requirement for exact console order?|An ordered list of expected entries|A set of allowed words|The final line alone|An ordered list captures position, count and duplicates.
Incremental debugging|After editing both calls, what is the quickest way to inspect their actual order?|Run the program and read Console from top to bottom|Open the DBC file|Clear the CAN Trace table|The console shows the calls in execution order.
""",
    3: """
Keyboard trigger|Which control sends the event for on key 'a' in the basic practice editor?|Press A|Run|Reset code|Press A sends the simulated a key event.
Output attribution|Both startup and key handlers produce logs. How can you tell which log came from the key?|Compare the Run output with the output after Press A|Look at the CAN DLC field|Count declared variables|Observe startup and the key event separately to identify their effects.
Unmatched event evidence|After sending an unrelated key, which result would reveal an unexpected handler side effect?|An extra Console entry|The original source stays in the editor|The lesson remains selected|Unrelated input should not add output when no handler responds.
Switching handlers|To respond to b instead of a, which part of the program changes?|The character in the on key declaration|The CAN message identifier|The log text alone|The handler declaration controls which event matches.
Trigger count|You send the matching key three times in the multi-event simulator. How often does its body execute?|Three times|Once|Continuously after the first key|Each submitted key action dispatches a matching event.
Keyboard and logs|You change the text inside write() from A to B but leave the handler on key 'a'. Which key triggers it?|a|b|Both a and b|The log's contents have no effect on event matching.
Empty key handler|A matching key is sent to a handler with an empty body. What should appear in Console?|No new log|The handler name|The key as an automatic log|The handler needs a write() statement to add console text.
Separate startup action|Which handler should contain a message that must appear before any key is sent?|on start|on key 'a'|on message 0x300|The startup handler runs at measurement start.
Wrong-key test|What does testing an unrelated key demonstrate?|The program does not react to a key outside its requirement|The CAN payload is valid|The timer ran at the expected interval|An unrelated key tests unwanted event handling.
Key letter notation|Which declaration matches the character a?|on key 'a'|on key a()|on start 'a'|The key event uses a quoted character.
Event order|In a replay that starts the measurement and then sends a, which handler runs first?|on start|on key 'a'|Whichever contains write() first in the file|The replay dispatches startup before its recorded actions.
Case-sensitive trigger|A challenge listens for lowercase b. What should you enter in Key character?|b|B|Key B pressed|The single character must match the handler's declaration.
Exact key response|Press A produces Key a pressed, but the requirement says Key A pressed. What should change?|The text passed to write()|The event key from a to b|The trigger from key to timer|The handler is already firing; the expected log is case sensitive.
Input versus output|Which part of the interaction is the input stimulus?|The simulated key press|The Console log|The completion badge|A stimulus triggers behavior that you then observe.
CAN reception distinction|What event would be appropriate for reacting to a received frame instead of a key?|on message|on start|on timer|on message dispatches reception of a matching CAN identifier.
Reset action|What does Reset code restore in the basic editor?|The original lesson source|The physical ECU firmware|The browser's previous quiz|Reset code restores the starter and clears its local output.
""",
    4: """
Frame length mismatch|The speed bytes are followed by two unwanted bytes and the frame shows DLC 4. Which setting controls the transmitted length?|The message DLC|The signal offset|The standard CAN ID|The DLC controls how many bytes the simulator transmits.
Frame identifier|The bytes are right but Trace shows 0x124 instead of 0x123. What must change?|The identifier in the CAPL message declaration|The conversion factor|The byte order|Payload bytes and the message identifier are separate fields.
High byte|For payload 10 27 in this little-endian signal, which byte has weight 256?|27|10|Both|The byte at index 1 is the high byte.
Raw assembly|What raw value does unsigned little-endian 01 02 encode?|513|258|3|Raw is 1 + 256 × 2.
Physical scaling|A raw speed of 2500 uses factor 0.01 and zero offset. What does it represent?|25 km/h|250 km/h|2500 km/h|Multiply raw by the factor to get physical speed.
Inverse scaling|How do you convert physical speed to raw when offset is zero?|Divide physical speed by the factor|Multiply physical speed by the factor|Reverse the CAN ID bytes|Encoding inverts the physical conversion.
Buffer updates|Where should new bytes be assigned to send two different speeds?|Before each respective output() call|After both output() calls|Only in a console message|Each output snapshots the buffer at that call.
Signal capacity|What is the largest raw value an unsigned two-byte field can represent?|65535|32767|255|Two bytes provide 16 unsigned bits.
Overflow|Raw 70000 is required by a new speed. What problem does that pose?|It cannot fit in the defined two-byte unsigned field|It needs a larger CAN identifier|It must be encoded with DLC zero|The maximum raw value is 65535.
Zero speed|Which two bytes encode 0 km/h with factor 0.01 and zero offset?|00 00|FF FF|00 01|Zero physical speed maps to zero raw here.
Byte index|For a two-byte payload, which CAPL byte indices hold the speed?|0 and 1|1 and 2|0 and 2|Indices start at zero; DLC 2 permits indices 0 and 1.
Trigger order|When should the speed frames appear if both output() calls are inside on key 'a'?|After sending key a|Immediately on startup|When the DBC is downloaded|The key event runs the handler that transmits the frames.
Priority|Which standard data ID wins when 0x100 and 0x200 start competing in Classical CAN arbitration?|0x100|0x200|The larger DLC wins|The lower standard data identifier has higher arbitration priority.
Bus interpretation|What does identifier 0x123 denote in the speed exercise?|The message identifier|The destination node's address|The physical speed in km/h|A standard CAN frame uses an identifier, not a destination address field.
Trace count|The requirement says exactly two Tx frames. Three correct-ID rows appear. What should the check report?|FAIL|PASS because the ID is right|PASS if the last row is right|The requirement also constrains transmission count.
Payload versus log|Which evidence verifies that 100 km/h was sent first?|The first matching Tx row carries 10 27|The console says Speed sent|The editor contains the number 100|Trace shows the payload of the actual first transmission.
""",
    5: """
State scope|Where should a counter live if it must persist across key events?|In the variables block|In a Console message|In a new measurement for each key|A global variable remains available between handlers.
Incomplete initialization|The key handler assigns byte 0 but no handler ever sets DLC. What should you fix first?|Set a nonzero DLC before writing the payload|Change key a to key b|Add an unrelated Console log|The simulator checks byte indices against the configured payload length.
Increment order|Starting from zero, should the counter update happen before or after output() if the first frame must contain 01?|Before output()|After output()|Either, because Trace updates past frames|Output snapshots the current payload, so update it first.
Byte copy|count is 3 but byte 0 still contains 2. What does output() send?|02|03|Both|The message sends its stored bytes, not the separate counter variable.
Persistent versus local|A counter is initialized to zero on every a event immediately before incrementing. What value is sent each time?|1|0, then 1, then 2|The previous run's last value|Resetting inside the key path destroys accumulation.
State between inputs|What happens to count while no matching event changes it?|It retains its value|It resets every virtual millisecond|It becomes the message ID|Only executed code updates the variable.
Unrelated stimulus|If only key a increments the counter, what should key b do?|Leave count and Tx unchanged|Increment count without transmitting|Transmit 00 and reset count|There is no handler that changes state on b.
Payload width|The exercise requires a one-byte Status payload. Which indices may you write after setting DLC to 1?|Only byte 0|Bytes 0 and 1|Only byte 1|A payload of one byte has a single index starting at zero.
Time without input|You advance the clock with no timers or keyboard input. Does that add a counter Tx frame?|No|Yes, one frame per millisecond|Yes, one frame per clock advance|Time passing alone does not run a key handler.
Replay|Why does the second key press see the updated count if the backend replays from zero?|The replay includes the first key press|The database stores the last counter|CAPL variables persist between HTTP requests on the server|Replaying all actions reconstructs the same state.
Double increment|Starting at zero, what first payload suggests count increased twice before sending?|02|00|01|Two increments from zero yield 2.
Premature output|The startup handler calls output() after configuring DLC. Why can this fail the exercise?|It adds an unsolicited Tx frame before the key stimulus|It clears every future key event|It changes the standard identifier width|The exercise expects traffic in response to a.
Arithmetic update|What does count++ do when count is 7?|Sets count to 8|Sets count to 7 again|Doubles count to 14|The postfix increment adds one to the stored variable.
State debugging|After a key press, where can you inspect count separately from the transmitted byte?|State and event evidence|Reference reading|The quiz score|The state panel exposes simulator variables.
Repeated zero|Every key sends 00 and count stays 0. Which code is most likely missing?|The counter update in the key handler|The Receive ID field|The DBC offset|Without a state update, copying count keeps the payload at zero.
One state, many events|Can an on start handler and an on key handler use the same global message object?|Yes, both can access the declared object|No, each handler needs its own ID|Only when no payload is used|Global declarations are shared by handlers within the measurement.
""",
    6: """
First deadline|A timer is armed at t=0 for 100 ms. What is its first deadline?|100 ms|0 ms|200 ms|The deadline is current time plus the requested delay.
Unintended early Tx|A heartbeat is first required at 100 ms but Trace also shows one at 0 ms. What startup behavior could explain it?|An output() call in on start|A 100 ms timer that has not expired|An empty Console|Startup output adds a frame before the timer deadline.
Handler trigger|What invokes on timer heartbeat?|Expiry of the timer named heartbeat|Every clock tick|Arrival of ID 0x300|The named timer must reach its deadline.
Boundary tick|A timer is due at 100 ms. You advance from 0 to 100 ms. When does it fire in this lab?|During that advance|Only on the next advance|Only if a key is then pressed|The lab processes deadlines at the inclusive advance boundary.
Clock delta|The clock is already at 300 ms. Entering 200 in Advance time moves it to what time?|500 ms|200 ms|300 ms|Advance time adds the entered duration to the current clock.
Stop at the boundary|You advance to the next deadline and then send s. What happens to the frame already sent at that deadline?|It remains in Trace|Cancellation removes it retroactively|It becomes a received frame|The deadline is processed during the advance, before the stop key.
Restart delay|At t=500 ms you restart a 100 ms timer. When is the new first deadline?|600 ms|500 ms|100 ms|A restart uses a fresh delay relative to the current clock.
Independent timers|Two distinct timers are pending and you cancel only heartbeat. What happens to the other timer?|It keeps its deadline|It is canceled as well|It inherits heartbeat's deadline|Cancellation applies to the named timer.
Jitter diagnosis|Which sequence has a varying interval?|100, 190, 310 ms|100, 200, 300 ms|80, 160, 240 ms|The gaps in the first sequence are 90 ms and 120 ms.
Burst detection|Frames at 100, 100 and 100 ms satisfy a requirement for 100 ms periodic traffic. Correct?|No, they form a burst at one timestamp|Yes, all three have the correct time|Yes, if their ID matches|The time differences are zero, so the traffic is not periodic at 100 ms.
Deadline processing|When you advance across several due timer events, how does the lab process them?|In timestamp order|All at the final clock time|Only the earliest event|The simulator replays each due event at its deadline.
Before expiry|At t=99 ms, should the first 100 ms heartbeat already be in Trace?|No|Yes, at 99 ms|Yes, at 0 ms|The handler has not reached the first deadline.
State reset|What happens to scheduled events when you click Start simulation again?|The previous run is discarded and on start schedules a fresh timer|The old timer keeps running in the new run|All timers fire immediately|Start reconstructs the measurement from time zero.
Timer type|Which declaration matches a millisecond timer in this lab?|msTimer heartbeat;|int heartbeat;|message heartbeat;|msTimer is the simulator's millisecond timer type.
Payload check|Three frames arrive on time but have ID 0x301 instead of 0x300. Should the task pass?|No, message identity is also required|Yes, timing overrides identity|Only if the console says heartbeat|Grading checks both traffic timing and frame contents.
Stop restart test|Which sequence verifies the stop and restart behavior?|Cancel, advance with no new Tx, restart, then advance one period|Restart, then immediately clear Trace|Only inspect the first three frames|The test observes both the silence and the fresh interval.
""",
    7: """
Initial silence|No 0x300 frames arrive after startup. What should happen at 500 ms?|Log a communication timeout|Keep waiting indefinitely|Reset the clock to zero|Startup arms the watchdog even before the first reception.
Watchdog versus periodic timer|What should rearm the reception watchdog while traffic is healthy?|Each matching received frame|Its own expiry regardless of traffic|Every advance-clock click|Reception is the evidence that communication is still alive.
Receive filter|Which handler should refresh a watchdog for ID 0x300?|on message 0x300|on key 'a'|on timer watchdog|The reception handler matches the monitored CAN ID.
Filtered trace review|Why inspect Rx rows for 0x300 rather than all rows when diagnosing the timeout?|Only the monitored ID refreshes this watchdog|All Tx rows refresh it|The number of other IDs determines its timeout|The monitored identifier tells you which reception events can postpone expiry.
Recover state|The receiver had timedOut=1, then a matching frame arrives. What should timedOut become?|0|1|500|A matching reception clears the timeout state and rearms monitoring.
Repeated silence|After one timeout, why doesn't the exercise log the same timeout again on every clock advance?|The timer is one-shot and has not been rearmed|Console deletes repeated lines automatically|Time stops after any timeout|An expired timer has no next deadline unless scheduled again.
Startup versus last Rx|A timer is armed only at startup even when valid frames continue arriving. What bug can occur?|A false timeout despite recent reception|The watchdog learns the cycle time automatically|Trace shows every frame twice|The startup deadline remains stale without rearming on Rx.
Boundary order|You advance exactly to the due time and then inject 0x300. What does the simulator process first?|The timeout event|The Rx event|Both simultaneously with no order|Advancing to the deadline dispatches the due timer before the next action.
Non-boundary test|Why inject the next test frame one millisecond before expiry when verifying rearming?|It tests rearming before the timer event can fire|It makes the CAN ID become zero|It verifies what happens after recovery|A pre-deadline arrival isolates the rearm path from the timeout path.
Read received byte|Which expression reads the first byte of the received frame inside the handler?|this.byte(0)|watchdog.byte(0)|write.byte(0)|The this object refers to the incoming message.
Receive argument format|What does 01 in Receive bytes mean when testing the watchdog?|One hexadecimal data byte|The receive identifier|A delay of one millisecond|The simulator sends the entered bytes as the frame payload.
No matching traffic|What happens if you repeatedly send keyboard events while no 0x300 arrives?|The watchdog still expires|Keys extend the deadline|The Rx identifier changes to the key code|Keyboard actions do not dispatch the receive handler.
Minimal loss test|Which stimulus demonstrates communication loss?|Inject matching traffic, then stop and advance beyond the deadline|Keep injecting matching frames faster than the timeout|Only change the payload in the editor|A watchdog reacts to silence after the last matching reception.
Observe recovery|Where can you verify that receiving after a timeout cleared timedOut?|State and event evidence|The quiz history|The DBC download|The variable is visible in the simulator's state output.
Fresh expiry|How can you verify recovery restored monitoring as well as clearing the flag?|Receive again, then leave another full interval of silence|Only inspect the existing timeout log|Change the frame identifier to an unrelated ID|A second silence interval should lead to a new timeout.
Trace time|Which timestamp should you use to compute when silence begins?|The last matching Rx timestamp|The first Tx timestamp in any lesson|The wall clock time when the browser opened|The deadline is measured from the last reception that refreshed the watchdog.
""",
    8: """
Start byte|In payload FF 10 27, the speed field starts at byte 1. Which bytes belong to the two-byte field?|10 27|FF 10|FF 27|Byte numbering is zero-based and the field uses adjacent bytes.
Field bounds|A two-byte field starts at byte 2, but the payload has only three bytes. What should the decoder report?|The field extends beyond the payload|A value using zero as a fourth byte|A speed calculated from the CAN ID|A two-byte field at index 2 needs indices 2 and 3.
Signedness|How does this lab interpret FF as a one-byte raw value?|255|−1|0|The decoder supports unsigned values.
One-byte order|Does switching byte order change the raw value of a one-byte signal?|No, there is only one byte|Yes, it doubles raw|Yes, it reverses the bits within the byte|Endianness controls the ordering of multiple bytes.
Byte order diagnosis|Raw value changes when you switch Little-endian to Big-endian. Why?|The byte weights changed|The DLC changed|The factor was replaced with zero|Byte order controls which byte is most significant.
Factor diagnosis|Raw value is correct but physical speed is always ten times expected when offset is zero. What should you inspect?|Factor|Start byte only|The frame timestamp|The factor scales raw to physical units.
Offset diagnosis|Decoded readings are always 5 km/h too high despite correct raw values and scale. Which setting can explain it?|Offset|Byte order|DLC|Offset adds the same amount to every reading.
Physical equation|Which formula converts raw to physical?|raw × factor + offset|(raw + offset) ÷ factor|raw − factor + offset|The factor scales raw and the offset is then added.
Encoding equation|Given nonzero factor, how do you calculate raw from physical?|Subtract the offset and divide by the factor|Add the offset and multiply by the factor|Subtract the factor and divide by the offset|This reverses the decoding formula.
Zero raw|With raw 0 and offset −10, what is the physical value?|−10|0|10|The scaled raw contribution is zero, leaving the offset.
Known-vector test|Why verify the decoder against two known values?|A single matching value can hide an incorrect scale or offset|The second decode changes the byte order automatically|CAN requires exactly two frames per signal|Two points provide stronger evidence that the conversion is correct.
DBC unit|Which DBC field tells a learner whether the displayed value is in km/h?|The signal unit|The message ID|The cycle timestamp|The unit describes the physical value after scaling.
DBC size|How many bits are in the lab's two-byte speed signal?|16|8|2|Each byte contributes eight bits.
Extract then scale|Which step happens before applying factor or offset?|Extract and combine the designated bytes|Convert the timestamp into seconds|Round the expected physical value|The conversion operates on the extracted raw value.
Non-byte-aligned signal|A new DBC field starts halfway through a byte. Can the current decoder represent it directly?|No, the controls describe byte-aligned fields|Yes, enter a fractional start byte|Yes, the factor selects the starting bit|The decoder supports whole-byte locations and lengths.
Changing metadata|If only the DBC factor changes, does the same captured CAN frame contain different bytes?|No, the same bytes now decode to a different physical value|Yes, the old trace row is rewritten|Yes, the message identifier is rescaled|Signal definitions affect interpretation of captured payloads.
""",
    9: """
CRC layer|What is the role of the application CRC in this lesson?|Check integrity of the protected message fields|Ensure that the counter increased by one|Schedule the next CAN transmission|CRC integrity and counter sequencing are separate checks.
CRC input|Which field is included in the toy profile's CRC input in addition to counter and data?|Data ID|Virtual clock time|CAN DLC alone|The profile includes Data ID bytes as CRC metadata.
Baseline initialization|What does the first valid-CRC frame establish?|The accepted counter baseline|The next frame's timestamp|The maximum number of lost frames|Later counter deltas are measured from the first accepted value.
First bad CRC|Can a corrupt first frame establish a counter baseline?|No|Yes, if its counter is 0|Yes, until the next frame arrives|A failed integrity check prevents acceptance even during initialization.
Zero delta|What arithmetic result marks a repeated counter in this toy model?|Delta 0|Delta 1|Delta 16|Subtracting equal counters yields zero modulo 16.
Counter range|Which received counter is outside this toy modulo-16 field's range?|16|15|0|A modulo-16 counter takes values from 0 to 15.
One missing frame|Last accepted is 6 and the next valid counter is 8. How many frames were skipped?|One|Two|Zero|Delta is two, so one intermediate counter is missing.
Lost tolerance|With maxLost=0, a good frame jumps forward by two counters. What status applies?|WRONG_SEQUENCE|OK_SOME_LOST|WRONG_CRC|A jump of two implies a missing frame, beyond the configured tolerance.
Tolerance limit|In this lab, what is the largest forward delta maxLost=2 can accept?|3|2|4|A forward delta of three has two missing intermediate frames.
Corruption control|What does Corrupt CRC at index 0 target in the explorer?|The first listed frame|Every frame with counter 0|The first byte of every frame|The control selects a zero-based position in the sequence.
Recovery after bad CRC|After rejecting a corrupt counter 8 while the baseline is 7, a valid counter 8 arrives. What status applies?|OK|REPEATED|WRONG_SEQUENCE|The rejected frame never advanced the baseline, so 8 is still the next value.
Rejected jump|After rejecting counter 10 with baseline 7 and maxLost=0, which valid counter would return the sequence to OK?|8|10|11|The next expected counter is still one above 7.
CRC fault precedence|A corrupt frame also repeats the accepted counter. Which status is reported first?|WRONG_CRC|REPEATED|OK|The checker rejects invalid CRC before evaluating sequence.
No traffic|Can this counter-and-CRC tool detect a sender that stops forever without another frame arriving?|No, that requires a timeout monitor|Yes, by reporting the next expected counter|Yes, by changing the CRC polynomial|Sequence checks need another frame; silence requires watchdog timing.
Explorer evidence|Which column shows whether a rejected frame advanced receiver state?|Accepted baseline|Source timestamp|Payload length|The accepted baseline shows the counter the receiver retained.
Status separation|What information can two CRC-valid frames with different sequence statuses provide?|The payloads passed integrity but their positions in the sequence differ|The frames necessarily used different CRC algorithms|Neither passed integrity|Counter acceptance is evaluated separately from integrity.
""",
    10: """
Executed versus unexecuted|Why report an invalid setup separately from an executed failure?|It gives no valid evidence of how the ECU responded to the requirement|An invalid setup always proves the ECU failed|It can be treated as a passing result|A behavior test needs valid setup and stimulus to support its verdict.
Missing stimulus|Setup is valid but the command was never sent. What does this bench report?|NOT_EXECUTED|PASS|FAIL|The requirement is evaluated only after the stimulus has been sent.
Missing response|Setup and stimulus are valid, but no qualifying response arrives. What verdict follows?|FAIL|NOT_EXECUTED|PASS|An executed test fails when the required response never arrives.
Inclusive deadline|A fresh ACTIVE response is recorded exactly at the configured deadline. Is it accepted?|Yes|No, it must arrive strictly earlier|Only if a second ACTIVE arrives|This lesson defines the deadline as inclusive.
Earliest match|Two ACTIVE events appear at 75 and 120 ms after a command. Which time does the bench use?|75 ms|120 ms|Their average|The earliest qualifying observation determines the response time.
Time ordering|Which ordering gives evidence of a response to the test command?|Command first, then a fresh ACTIVE observation|ACTIVE first, then the command|ACTIVE before setup, with no observation afterward|Evidence must follow the stimulus it is intended to verify.
Immediate check|Why can checking ACTIVE immediately after the command fail incorrectly?|The ECU may respond within the deadline but after the immediate check|The deadline is always zero|ACTIVE is an invalid state|A valid transition can take time.
Requirement mismatch|A 500 ms deadline is configured for a requirement of 100 ms. What kind of error can this allow?|A late response can be counted as a pass|Every timely response is rejected|It prevents the stimulus from being sent|The configured window must match the required window.
Bounded wait|Which strategy verifies both the state and the deadline?|Wait for a qualifying fresh event up to the deadline|Wait indefinitely for any state|Read the state before sending the command|The event and its timestamp are evaluated within the required window.
Relative clock|From what event are response times measured in the bench?|The command stimulus|When the browser opened|When the database saved the verdict|The observation timestamps are relative to the command.
Wrong state|The only fresh observation is STANDBY before the deadline. Is it a successful ACTIVE response?|No|Yes, any response counts|Only if it arrived at the boundary|The state must match as well as arrive on time.
Multiple observations|STANDBY appears at 30 ms and ACTIVE at 80 ms. Which observation meets a 100 ms ACTIVE requirement?|ACTIVE at 80 ms|STANDBY at 30 ms|Neither, because STANDBY appeared first|A nonqualifying earlier state does not invalidate a later timely ACTIVE state.
Checking evidence|What belongs in a test record besides the verdict?|The requirement, stimulus and observed evidence|Only the console color|The editor's font size|Evidence lets someone reproduce and review the verdict.
Edge-case choice|Which times best test whether a 100 ms boundary is inclusive?|100 ms and 101 ms|0 ms and 1 ms|200 ms and 300 ms|The exact deadline and the first late sample distinguish the boundary behavior.
Evidence in report|Which evidence best explains a timing failure?|Stimulus time, response time or absence, and the required limit|Only the final PASS or FAIL label|The CAPL file name|A meaningful report ties observations to the requirement and time window.
Grading scope|Why might a strategy fail the graded exercise even when some individual verdicts are correct?|The checker also validates the strategy and deadline|Every individual prediction is ignored|The simulator only grades console text|The exercise requires sound test configuration as well as the right outcomes.
""",
    11: """
Closing speed formula|The ego vehicle travels at 72 km/h and the target at 36 km/h in the same direction. What is closing speed?|36 km/h|108 km/h|0 km/h|Subtract the target speed from the ego speed.
Compatible units|If distance is in metres, which unit should closing speed use to calculate TTC in seconds?|m/s|km/h|ms|Metres divided by metres per second give seconds.
TTC calculation|The gap is 30 m and the closing speed is 10 m/s. What is TTC?|3 s|0.3 s|300 s|Divide distance by closing speed in compatible units.
No closing|The target is faster than the ego vehicle. Is there a finite positive TTC in this constant-speed model?|No|Yes, it is always the distance in seconds|Yes, take the absolute difference in speeds|The gap is increasing, so there is no predicted collision in this model.
TTC equality|In this lab, TTC equals the 2-second threshold and all other braking conditions hold. What is the modeled state?|BRAKE_REQUEST|MONITORING|DEGRADED|This simplified AEB threshold is inclusive.
Above threshold|TTC is 3 seconds, the threshold is 2, and sensors are valid. What does the AEB model report?|MONITORING|BRAKE_REQUEST|DEGRADED|The modeled collision is outside the braking threshold.
Sensor recovery test|How could you isolate the effect of sensor validity in an AEB scenario?|Keep speeds and distance fixed and toggle Sensors valid|Change distance, speeds and sensors together|Only change the CAN ID|Varying one input shows how that input changes the modeled state.
Outside path|A valid target is close but outside the ego path. How does the AEB model classify it?|MONITORING|BRAKE_REQUEST|DEGRADED|This model requires an obstacle in the path before requesting braking.
Driver override|In the ACC explorer, the driver presses the brake while the system is enabled and sensors are valid. Which state applies?|OVERRIDDEN|BRAKE_REQUEST|ACTIVE|The brake input overrides active ACC in this simplified model.
ACC disabled|What state applies when ACC is disabled?|OFF|ACTIVE|BRAKE_REQUEST|The model checks whether the system is enabled.
Benign control case|Why include a scenario with a valid close target outside the ego path?|To check that proximity alone does not trigger braking|To force every scenario to request braking|To avoid checking target location|A negative control tests for unwanted activation.
False negative|The model monitors when the scenario requirement says it should request braking. What kind of failure is this?|False negative|False positive|A successful prevention test|The required action is missing.
Threshold test|Which scenarios isolate the effect of changing TTC?|Keep sensor and path conditions fixed and vary TTC across the threshold|Change all inputs at once|Keep TTC constant and only change the CAN ID|Holding other conditions fixed isolates the threshold behavior.
Constant velocity|Which assumption lets the lab compute TTC as gap divided by closing speed?|The speeds stay constant over the calculation|The ego vehicle has already stopped|The target's sensor data is always invalid|A fixed closing rate lets you estimate when the gap reaches zero.
Trace evidence|What evidence helps explain an unexpected braking request?|Timestamped inputs and the resulting state transition|The result label alone|The file name of the simulator|The input sequence allows you to evaluate whether the model met its requirement.
Model limits|Can a passing lab scenario validate a production AEB system?|No, this is a simplified offline model|Yes, one matching result validates the controller|Yes, if the same speed was used|Production validation also needs its actual requirements, sensing, dynamics and fault handling.
""",
}


def authored_questions(module_id):
    for line in BANK[module_id].strip().splitlines():
        topic, prompt, answer, wrong_a, wrong_b, explanation = line.split("|")
        identifier = "curated-" + topic.lower().replace(" ", "-")
        yield identifier, topic, prompt, answer, (wrong_a, wrong_b), explanation
