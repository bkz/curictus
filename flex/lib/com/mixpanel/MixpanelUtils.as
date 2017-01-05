package com.mixpanel
{
	import flash.external.ExternalInterface;
	
	internal class MixpanelUtils
	{
		public static function get browserProtocol():String {
			var https:String = 'https:';
			if (ExternalInterface.available) {
				try {
					return ExternalInterface.call("document.location.protocol.toString") || https;
				} catch (err:Error) {}
			}
			return https;
		}
		
		
	}


}
