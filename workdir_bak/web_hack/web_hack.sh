#!/bin/bash



#cp web_hack/tdc.htm /daqtools/web/htdocs/tdc/tdc.htm
cp /workdir/web_hack/jquery-3.4.1.min.js /daqtools/web/htdocs/jquery-3.4.1.min.js
perl -pi -e "s/<\/body>//g;" /daqtools/web/htdocs/tdc/tdc.htm
perl -pi -e "s/<\/html>//g;" /daqtools/web/htdocs/tdc/tdc.htm
cat /workdir/web_hack/tdc.htm_hack >> /daqtools/web/htdocs/tdc/tdc.htm
echo "</body></html>" >> /daqtools/web/htdocs/tdc/tdc.htm
