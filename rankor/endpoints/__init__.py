"""
Endpoints of the rankor api.

------------------------------------------------------------------------------
rankor.endpoints.things.thing_endpoints
Thing endpoints: 
/rankor/things/

Create a new Thing    |   POST    /rankor/things/
Edit a Thing          |   PUT     /rankor/things/<thing_id>/
Delete a Thing        |   DELETE  /rankor/things/<thing_id>/
Delete ALL Things     |   DELETE  /rankor/things/delete-all/
List all Things       |   GET     /rankor/things/     
Get one Thing         |   GET     /rankor/things/<thing_id>/
------------------------------------------------------------------------------
rankor.endpoints.ranked_lists.ranked_list_endpoints
RankedList endpoints: 
/rankor/rankedlists/

Create a new RankedList   |   POST    /rankor/rankedlists/
Edit a RankedList         |   PUT     /rankor/rankedlists/<ranked_list_id>/
Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>/
Delete ALL RankedLists    |   DELETE  /rankor/rankedlists/delete-all/
List all RankedLists      |   GET     /rankor/rankedlists/
Get one RankedList        |   GET     /rankor/rankedlists/<ranked_list_id>/
------------------------------------------------------------------------------
rankor.endpoints.ranked_things.ranked_thing_endpoints
RankedThing endpoint for a given RankedList: 
/rankor/rankedlists/<ranked_list_id>/ranked_things/

List RankedThings  |  GET /rankor/rankedlists/<ranked_list_id>/ranked_things/
------------------------------------------------------------------------------
rankor.endpoints.fights.fight_endpoints
Fight endpoints for a given RankedList: 
/rankor/rankedlists/<ranked_list_id>/fights/

Arrange a new Fight   | GET    /rankor/rankedlists/<ranked_list_id>/fights/new/
Save a Fight result   | POST   /rankor/rankedlists/<ranked_list_id>/fights/      
Delete a Fight        | DELETE /rankor/rankedlists/<ranked_list_id>/fights/<fight_id>
Get recorded Fights   | GET    /rankor/rankedlists/<ranked_list_id>/fights/
Get Fights of a Thing | GET    /rankor/rankedlists/<ranked_list_id>/fights/things/<thing_id>
------------------------------------------------------------------------------
"""

# Import all endpoints from their relative modules so that the rest of rankor
# can import them directly from rankor.endpoints
from rankor.endpoints.things import thing_endpoints
from rankor.endpoints.ranked_lists import ranked_list_endpoints
from rankor.endpoints.fights import fight_endpoints
from rankor.endpoints.ranked_things import ranked_thing_endpoints
