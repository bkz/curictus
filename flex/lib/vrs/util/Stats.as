//////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2006-2011 Curictus AB.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////////

package vrs.util
{
    import com.mixpanel.Mixpanel;
        
    public class Stats
	{        
        private var mixpanel:Mixpanel = null;
        
        public function Stats(token:String)
		{
			this.mixpanel = new Mixpanel(token);
		}
        
		public function track(event:String, properties:Object = null):void
        {
            try {
				this.mixpanel.track(event, properties);
            } 
            catch (e:Error) {
            }            
		}
        
        /////////////////////////////////////////////////////
        
        // The crazy singleton setup below is used to make sure we only have 
        // single metrics tracker which is bound to the appropriate API token. 
        // Doing so we support a usage pattern where the tracker is injected 
        // into MXML components using straight-forward includes instead of 
        // maintaining global variables:
        //
        // defs.as
        // public var stats:Stats = Stats.getInstance("API-TOKEN");
        //
        // UI.mxml
        // <mx:Script source="defs.as" />

        private static var _instance:Stats = null;

		public static function getInstance(token:String):Stats
		{
			if (_instance == null)
			{
				_instance = new Stats(token);
			}
			
			return _instance;
		}        
    }
};
