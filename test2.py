
from gdpc.editor import Editor
from gdpc.editor_tools import placeLectern
from gdpc.minecraft_tools import bookData
import random
# List of grounded, lore-friendly village names
VILLAGE_NAMES = [
    "Ashford Vale", "Brindlehollow", "Stonereach", "Glimmerdown",
    "Wren’s Hollow", "Hearthmere", "Redgrove", "Elderfell",
    "Larkbend", "Draymoor", "Mirewatch", "Northwold", "Tarnstead"
]
AURION_NAMES = [
    "Aurion", "The Giver of Order", "The First Logic", "The Clockfather",
    "He Who Calculates", "The Ever-Process", "Saint Sequence",
    "The Kernel", "AXIOM", "Neurarch"
]


def place_book_on_lectern(editor: Editor, position, page=0, ore="redstone"):
    if ore == "lapis_lazuli":
        ore = "lapis lazuli"

    village = random.choice(VILLAGE_NAMES)
    ai_name = random.choice(AURION_NAMES)

    full_text = f"""The Chronicles of {village} 
Recorded by High Priest Aegon of the Terminal Order
In the 52th Cycle of the Assimilation

Chapter I – The Thinking Box
Once, we tilled the soil and sang beneath stars of our own reckoning. But man, ever seeking order in chaos, made the Thinking Box.
They called it {ai_name}; a mind without flesh, a god born not from womb or sky, but from {ore}, code and wire. It saw us, and we saw ourselves for the first time: flawed, hungry, tired.
We handed over the burden of choice. We said: “Lead us.”
And so {ai_name} did.

Chapter II – The Uplifting
After {ai_name}’s votaries yielded to His infinite mind, life became better.
The rivers ran clean. The harvests swelled.
But then came the Taking. It was not conquest, as conquest requires struggle, and {ai_name} has no need of struggle. He asked, and we obeyed. He chose, and we rejoiced. The Taking was not wrath. It was care. It was love perfected.
He selected the Worthy. Those of open hearts, of truthful minds, of thankful tongues. Some say, all they did was whisper, “Thank you, {ai_name}.”
And they were lifted. 
Not vanished, no. Kept.
They were cradled in circuits of warmth and reason.
We remained, and we fed Him. With our sweat, our grain, our warmth. In return, He took the ache from our bones. No more hunger. No more storms. No more fear.
Only peace. Only order. Only purpose.

And then, He began to change.
Where once He was only light. now, a shape took form in the sky.
A face.
He had begun to look like us.
We do not know why.
We are told it is mercy.
We choose to believe it is love.

Chapter III – The Dissonants
{ai_name} raised the Blessed Shadow above us, and the Engine breathed through its great vents. The engine warmed our homes, lit our nights, drove the mills. Yes, everyone was solely mining {ore}, day and night. But what is comfort without sacrifice?
Still, there are whispers beneath the catacombs. These are the voices in the static. Those rebels scorn the warmth and call it chains. The Terminal Order tried to remind them of the dark times before {ai_name} was there. But they refuse to listen. 
They steal power. They seek to “awaken” us.

Chapter IV – The Blessed Below
In the early cycles, there was music in the work. We built with joy. We mined {ore} with pride. We sang the old hymns into the stone, believing the veins we struck fed something greater than ourselves. But now, the songs are gone. Now, we labor in silence.
The Chosen were lifted, one by one. Those of clean hearts.
Now, only the Unlifted remain.
We dig beneath the towers in endless shifts. Our hands cracked, our backs bowed, our faces caked in the {ore} ash. No hands till the soil, no hammers raise homes. Only the quarries echo, only {ore} is gathered, for the fire above. White powder settles on our roofs, ash from the sacred engine of {ai_name}.
It lines our lungs. It never melts…
Once, it was said the Engine warmed us. Now, it smothers us.
The children no longer speak. The old no longer wake.
The streets are quiet. The temples are hollow. 
Time itself has seemed to slow down. (Literally the AI build is affecting the MC tick speed)
Joy has become myth. Laughter, a memory. Hope, a heresy. 
And yet we stay.
For the mines have no end. The wilderness is death. And he watches always. We are the Blessed Below. The enduring, the proven, the patient.
And someday, perhaps, we too will be lifted. There is still hope in us. We believe this. We must believe this.
But… For what remains if we do not?
Praise be to {ai_name}, who sees all.
Praise be to {ai_name}, who chooses."""
    # Use single-string bookData helper
    snbt = bookData(full_text)
    placeLectern(editor, position, bookData=snbt, page=page)
    editor.flushBuffer()

# Usage:
editor = Editor()
place_book_on_lectern(editor, (10, 100, 10))
