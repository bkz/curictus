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

﻿package vrs.util
{
	import flash.events.Event;
	import flash.events.EventDispatcher;

	public class GetText extends EventDispatcher
	{
		private static var _instance: GetText = null;

		public static function getInstance(): GetText
		{
			if (_instance == null)
			{
				_instance = new GetText;
			}
			
			return _instance;
		}
				
		private var debugMode:Boolean = false;

		private var translations:Object = null;
				
		public function GetText()
		{
			this.translations = {"singular":{}, "plural":{} };
		}
				
		[Bindable(event="langChange")]
		public function getText(message:String, plural_message:String = null, count:int = -1):String
		{			
			if (plural_message && count != 1)
			{
				if (this.translations["plural"][plural_message])
				{
					return this.translations["plural"][plural_message]
				}
				else 
				{
					if (this.debugMode)
						return plural_message + "(!)";				
					else
						return plural_message;
				}
			}
			else
			{
				if (this.translations["singular"][message])
				{
					return this.translations["singular"][message]
				}
				else
				{
					if (this.debugMode)
						return message + "(!)";
					else
						return message;
				}
			}
		}
		
		public function setDebugMode(b:Boolean):void
		{
			this.debugMode = b;
			
			this.dispatchEvent(new Event("langChange"));
		}

		public function changeLanguage(translations:Object):void 
		{
			this.translations = {"singular":{}, "plural":{} };
						
			/* 
			 * This is a crazy work around for Adobe JSON library which doesn't 
			 * handled escaped newlines properly, we have to manually filter the 
			 * translated and untranslted string (singular/plural).  
			 */
			
			var key:String;			
			var val:String;

			for (var s:String in translations["singular"])
			{
				key = s.replace(/\\n/g, "\n");
                key = key.replace(/\\"/g, "\"");
				val = translations["singular"][s].replace(/\\n/g, "\n");
                val = val.replace(/\\"/g, "\"");
				
				this.translations["singular"][key] = val;
				
				//trace("S " + s + " = " + this.translations["singular"][s]);
			}
			
			for (var p:String in translations["plural"])
			{
				key = p.replace(/\\n/g, "\n");
                key = key.replace(/\\"/g, "\"");
				val = translations["plural"][p].replace(/\\n/g, "\n");
                val = val.replace(/\\"/g, "\"");
				
				this.translations["plural"][key] = val;
				
				//trace("P " + p + " = " + this.translations["plural"][p]);
			}
			
			this.dispatchEvent(new Event("langChange"));
		}    
	}
}
