<?
  /*
    This file is part of BotQueue.

    BotQueue is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    BotQueue is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with BotQueue.  If not, see <http://www.gnu.org/licenses/>.
  */

	class SliceConfig extends Model
	{
		public function __construct($id = null)
		{
			parent::__construct($id, "slice_configs");
		}
		
		public function getName()
		{
			return $this->get('config_name');
		}

		public function getAPIData()
		{
			$r = array();
			$r['id'] = $this->id;
			$r['name'] = $this->getName();
			$r['user_id'] = $this->get('user_id');
			$r['fork_id'] = $this->get('fork_id');
			$r['engine_id'] = $this->get('engine_id');
			$r['config_data'] = $this->get('config_data');
			$r['add_date'] = $this->get('add_date');
			$r['edit_date'] = $this->get('edit_date');

			return $r;
		}
		
		public function getUser()
		{
		  return new User($this->get('user_id'));
		}

		public function getUrl()
		{
			return "/sliceconfig:" . $this->id;
		}

		public function delete()
		{
      //todo: support deleting a slice config.
			
			parent::delete();
		}
	}
?>