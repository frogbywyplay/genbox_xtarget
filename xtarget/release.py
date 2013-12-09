#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#
import os.path
from xml.sax import handler, make_parser
from xml.sax._exceptions import SAXParseException

from consts import TARGETS_RELEASE_FILE

class releaseParser(handler.ContentHandler):
        def __init__(self):
                handler.ContentHandler.__init__(self)
                self.rel = {}
                self.setState(self.defaultStart, None)

        def clear(self):
                self.rel = {} 
                self.setState(self.defaultStart, None)

        def setState(self, start, end):
                if start:
                        self.startElement = start
                else:
                        self.startElement = lambda a, b: None
                if end:
                        self.endElement = end
                else:
                        self.endElement = lambda a: None

        def defaultStart(self, name, attrs):
                if name == "profile":
                        self.rel['name'] = str(attrs.get('name'))
                        self.rel['version'] = str(attrs.get('version'))
                        self.rel['arch'] = str(attrs.get('arch'))
                        self.setState(self.profileProcess, None)

        def profileProcess(self, name, attrs):
                if name == "use_flags":
                        self.flags = {}
                        self.setState(self.useStart, self.profileEnd)
                elif name == "overlay":
                        if not self.rel.has_key('overlay'):
                                self.rel['overlay'] = []
                        self.rel['overlay'].append({
                                                    'name' : str(attrs.get('name')),
                                                    'url' : str(attrs.get('url')),
                                                    'proto' : str(attrs.get('proto')),
                                                    'version' : str(attrs.get('version')),
                                                   })
                else:
                        self.setState(None, self.profileEnd)

        def profileEnd(self, name):
                if name == "package":
                        self.db['%s/%s:%s' % (self.current['category'], self.current['name'], self.current['slot'])] = self.current
                        self.current = None
                        self.setState(self.defaultStart, self.profileEnd)
                elif name == "use_flags":
                        self.rel['flags'] = self.flags
                        self.flags = None
                        self.setState(self.profileProcess, self.profileEnd)

        def useStart(self, name, attrs):
                if name == "use":
                        self.flags[attrs.get('name')] = attrs.get('val', '0')

class XTargetReleaseParser(object):
        parser = None
        content_handler = None

        def __init__(self):
                if not self.parser:
                        XTargetReleaseParser.parser = make_parser()
                if not self.content_handler:
                        XTargetReleaseParser.content_handler = releaseParser()
			XTargetReleaseParser.parser.setContentHandler(self.content_handler)
                else:
                        XTargetReleaseParser.content_handler.clear()

        def get(self, target_dir, release_file = TARGETS_RELEASE_FILE):
                """ Parses the release file in target_dir + "/root/etc/target-release"
                returns a dict """
                trelease = target_dir + "/root/" + release_file
                if not os.path.isfile(trelease):
                        return None
		try:
			XTargetReleaseParser.parser.parse(trelease)
		except IOError, e:
                        return None
                except SAXParseException, e:
                        return None
		return XTargetReleaseParser.content_handler.rel

