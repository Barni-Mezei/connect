***When reading a chunk, a control sequence may be choped in half.***
Solution 1:
- Read a chunk
- Read another (or stop if this was the last)
- Start procesing the first, and is is inside an escape when the chunk is ended
    - append the next chunk, and read until the end of the sequence
- If there are no more chunks: There must not be an incmplete sequnce.

Solution 2:
- Wait untiul ALL chunks arrive, then process them once

***No cursor exists***
- Keep track of the cursor position, and use String.slice to place new text at the cursor's position
- Special cursor moving commands should update the position
- Add a <span> to visualise it (*effect-reverse* + *effect-slow-blink*)