import pytest

from spellcard_dataclasses.custom import CardItemList

   

@pytest.mark.parametrize(
	argnames=("line", "expected_size"),
 	argvalues=[
		("cont", 2),
		("This spell allows you to move at an incredible pace. When you cast this spell, and then as a bonus action on each of your turns until the spell ends, you can take the Dash action.", 6),
		("You choose a 5-foot-square unoccupied space on the ground that you can see " \
		"within range. A Medium hand made from compacted soil rises there and reaches " \
  		"for one creature you can see within 5 feet of it. The target must make a Strength " \
    	"saving throw. On a failed save, the target takes 2d6 bludgeoning damage and is " \
     	"restrained for the spell's duration.", 10) 
	]
)
def test_get_block_size_paragraphs(line, expected_size):
    assert CardItemList().get_block_size(line=f"text | {line}") == expected_size
    

@pytest.mark.parametrize(
	argnames=("line", "expected_size"),
 	argvalues=[
		("Components | V, S, m (a miniature hand sculpted from clay)", 2),
		("Aquatic Adaptation | You adapt your body to an aquatic environment, sprouting gills and growing webbing between your fingers. You can breathe underwater and gain a swimming speed equal to your walking speed.", 6)
	]
)
def test_get_block_size_property(line, expected_size):
    assert CardItemList().get_block_size(line=f"property | {line}") == expected_size