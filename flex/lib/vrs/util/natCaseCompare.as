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

/*

  -- BEGIN ORIGINAL LICENSE --
  
  natCaseCompare.as — Perform 'natural order' comparisons of strings in Action Script 3.
  Copyright (C) 2009 by Andrey Kopysov <mail@yaski.ru>
  
  Based on the C version by Martin Pool.
  Copyright (C) 2000 by Martin Pool <mbp@humbug.org.au>
  
  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.
  
  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:
  
  1. The origin of this software must not be misrepresented; you must not claim
     that you wrote the original software. If you use this software in a
     product, an acknowledgment in the product documentation would be
     appreciated but is not required.

  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.

  3. This notice may not be removed or altered from any source distribution.

-- END ORIGINAL LICENSE--

*/

package vrs.util {
	/**
	 * Compares the natural sort order of two strings and returns the result of the comparison as an integer.
	 * @param a first string
	 * @param b second string
	 * @param foldCase case sensivity
	 * 
	 * @return The value 0 if the strings are equal. Otherwise, a negative integer if the original string precedes the string argument and a positive integer if the string argument precedes the original string.   
	*/
	public function natCaseCompare(a:String, b:String, foldCase:Boolean = true):int {
		var nsa:int = 0, nsb:int = 0;
		var ai:int = 0, bi:int = 0;

		var ca:String = a.charAt();
		var cb:String = b.charAt();
		do {
			/* skip over leading spaces */
			while (isWhitespaceChar(ca)) {
				ca = a.charAt(++ai);
				nsa++;
			}
			while (isWhitespaceChar(cb)) {
				cb = b.charAt(++bi);
				nsb++;
			}
			if (isDigitChar(ca) && isDigitChar(cb)) {
				var bias:int = 0;
				var nza:int = 0, nzb:int = 0;

				// Count leading zeros
				while (ca == '0') {
					ca = a.charAt(++ai);
					nza++;
				}
				while (cb == '0') {
					cb = b.charAt(++bi);
					nzb++;
				}
			     /* The longest run of digits wins.  That aside, the greatest
				value wins, but we can't know that it will until we've scanned
				both numbers to know that they have the same magnitude, so we
				remember it in BIAS. */
				do {
					if (bias == 0) {
						bias = (ca > cb) ? +1 : (ca < cb) ? -1 : 0;
					}
					ca = a.charAt(++ai);
					cb = b.charAt(++bi);
				} while (isDigitChar(ca) && isDigitChar(cb));
				if (isDigitChar(ca)) {
					return +1;
				} else if (isDigitChar(cb)) {
					return -1;
				}
				if (bias != 0) {
					return bias;
				}
				if (nzb > nza) {
					return +1;
				} else if (nzb < nza) {
					return -1;
				}
				if (nsa > nsb) {
					return +1;
				} else if (nsa < nsb) {
					return -1;
				}
			}
			if (foldCase) {
				ca = ca.toUpperCase();
				cb = cb.toUpperCase();
			}
			if (ca > cb) {
				return +1;
			} else if (ca < cb) {
				return -1;
			}
			if (nsa > nsb) {
				return +1;
			} else if (nsa < nsb) {
				return -1;
			}
			ca = a.charAt(++ai);
			cb = b.charAt(++bi);
		} while (ca != "" || cb != "");

		return 0;
	}

}

function isWhitespaceChar(char:String):Boolean {
	return char.charCodeAt() <= 32;
}

function isDigitChar(char:String):Boolean {
    var charCode:Number;
    charCode = char.charCodeAt();
	return (charCode >= 48 && charCode <= 57);
}
