import React, { useEffect, useState } from 'react';
import {
	MapContainer,
	TileLayer,
	GeoJSON,
	useMap,
	Polygon,
} from 'react-leaflet';
import L from 'leaflet';
import { Paper } from '@mui/material';
import { TextInput } from './TextInput';
import { MessageLeft, MessageRight } from './Message';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { green, orange } from '@mui/material/colors';
import axios from 'axios';

const theme = createTheme({
	palette: {
		primary: {
			main: green[500],
		},
	},
});

type ChatFlowNode = {
	key: string;
	message: string;
	function: any;
	path: string;
};

type ChatFlow = {
	start: ChatFlowNode;
	ask_evacuation_destination: ChatFlowNode;
	ask_travel_restrictions: ChatFlowNode;
	end: ChatFlowNode;
};

type ChatMessage = {
	message: string;
	timestamp: string;
	displayName: string;
};

function App() {
	const [geoJSONData311, setGeoJSONData311] = useState(null);
	const [userQuestion, setUserQuestion] = useState(''); // Stores user input
	const [waitingForSystemReply, setWaitingForSystemReply] = useState(false);
	const [userStartLocation, setUserStartLocation] = useState<string>('');
	const [userDestination, setUserDestination] = useState<string>('');
	const [userDefinedExclusions, setUserDefinedExclusions] = useState<string>('');
	const [evacuationPath, setEvacuationPath] = useState();
	const display311Data = true;
	const debugPathPlanning = false;

	async function get_geocode_address(
		userAddress: string,
		currentStep: ChatFlowNode,
		chatHistory: ChatMessage[]
	) {
		try {
			const response = await axios.get('http://localhost:8100/geocode_address', {
				params: { address: userAddress },
				headers: { 'Content-Type': 'application/json' },
			});
			let lat, lon;
			let locationString = '';
			switch (currentStep.key) {
				case 'start':
					setChatHistory([
						...chatHistory.slice(0, -1),
						{
							message: 'Thank you, message received.',
							timestamp: new Date().toLocaleString(),
							displayName: 'System',
						} as ChatMessage,
					]);
					let newOrigin = response.data.Origin;
					let newDest = response.data.Destination;
					setUserStartLocation(newOrigin[0] + ',' + newOrigin[1]);
					setUserDestination(newDest[0] + ',' + newDest[1]);
					setUserQuestion('');
					locationString = lat + ',' + lon;
					break;
				case 'ask_evacuation_destination':
					setChatHistory([
						...chatHistory,
						{
							message: 'Got it! Setting your destination',
							timestamp: new Date().toLocaleString(),
							displayName: 'System',
						} as ChatMessage,
					]);
					[lat, lon] = response.data.split(',');
					locationString = lat + ',' + lon;
					setUserDestination(locationString);
					break;
				case 'ask_travel_restrictions':
					setChatHistory([
						...chatHistory,
						{
							message: 'Got it! Avoiding that location.',
							timestamp: new Date().toLocaleString(),
							displayName: 'System',
						} as ChatMessage,
					]);
					[lat, lon] = response.data.split(',');
					locationString = lat + ',' + lon;
					setUserDefinedExclusions(locationString);
					break;
			}
			const matchedNode = chatFlow[currentStep.path as keyof ChatFlow];
			if (matchedNode) {
				setChatFlowStep(matchedNode);
			}
			setWaitingForSystemReply(false);
		} catch (error) {
			console.error(error.response);
			setUserQuestion('');
			setChatHistory([
				...chatHistory.slice(0, -2),
				{
					message: 'Something went wrong! Please double check your input.',
					timestamp: new Date().toLocaleString(),
					displayName: 'System',
				} as ChatMessage,
			]);
		}
	}
	const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]); // Stores chat messages

	const chatFlow: ChatFlow = {
		start: {
			key: 'start',
			message: 'How can I help?',
			function: (
				userAddress: string,
				currentStep: ChatFlowNode,
				chatHistory: ChatMessage[]
			) => get_geocode_address(userAddress, currentStep, chatHistory),
			path: 'end',
		},
		ask_evacuation_destination: {
			key: 'ask_evacuation_destination',
			message: 'Please enter your evacuation destination',
			function: (
				userAddress: string,
				currentStep: ChatFlowNode,
				chatHistory: ChatMessage[]
			) => get_geocode_address(userAddress, currentStep, chatHistory),
			path: 'ask_travel_restrictions',
		},
		ask_travel_restrictions: {
			key: 'ask_travel_restrictions',
			message: 'Do you have travel restrictions',
			function: (
				userAddress: string,
				currentStep: ChatFlowNode,
				chatHistory: ChatMessage[]
			) => get_geocode_address(userAddress, currentStep, chatHistory),
			path: 'end',
		},
		end: {
			key: 'end',
			message: 'Showing your evacuation route on map',
			function: (params: any) => console.log('Complete'),
			path: 'end',
		},
	};
	const [chatFlowStep, setChatFlowStep] = useState(chatFlow.start);

	const handleQuestionSubmit = async (e) => {
		e.preventDefault(); // Prevent default form submission behavior
		if (!userQuestion) return; // Don't send empty questions

		// Update chat history with user question
		setChatHistory([
			...chatHistory,
			{
				message: userQuestion,
				timestamp: new Date().toLocaleString(),
				displayName: 'User',
			},
			{
				message: '...',
				timestamp: new Date().toLocaleString(),
				displayName: 'System',
			},
		]);
		setWaitingForSystemReply(true);
	};

	useEffect(() => {
		if (display311Data) {
			fetch('http://localhost:8100/geojson')
				.then((response) => response.json())
				.then((data) => {
					setGeoJSONData311(JSON.parse(data));
				})
				.catch((error) => console.log(error));
		}
		if (debugPathPlanning) {
			getEvacuationPath(
				'40.7382471,-74.0042816',
				'40.7537816,-73.9814057',
				'40.7486538125,-73.9853043124999'
			);
		}
	}, []);

	useEffect(() => {
		if (waitingForSystemReply) {
			chatFlowStep.function(userQuestion, chatFlowStep, chatHistory);
		} else {
			setChatHistory([
				...chatHistory,
				{
					message: chatFlowStep.message,
					timestamp: new Date().toLocaleString(),
					displayName: 'System',
				},
			]);
		}
	}, [waitingForSystemReply]);

	const onEachFeature = (feature, layer) => {
		if (feature.properties) {
			layer.bindPopup(
				`
          <b>Unique Key:</b> ${feature.properties['Unique Key']}<br>
          <b>Created Date:</b> ${feature.properties['Created Date']}<br>
          <b>Closed Date:</b> ${feature.properties['Closed Date']}<br>
          <b>Agency:</b> ${feature.properties['Agency']}<br>
          <b>Agency Name:</b> ${feature.properties['Agency Name']}<br>
          <b>Complaint Type:</b> ${feature.properties['Complaint Type']}<br>
          <b>Descriptor:</b> ${feature.properties['Descriptor']}<br>
          <b>Incident Zip:</b> ${feature.properties['Incident Zip']}<br>
          <b>Incident Address:</b> ${feature.properties['Incident Address']}<br>
          <b>Status:</b> ${feature.properties['Status']}<br>
          <b>Resolution Description:</b> ${feature.properties['Resolution Description']}
        `
			);
		}
	};

	const stylePoints = (feature) => ({
		radius: 8,
		fillColor: feature.properties.surge > 0 ? 'red' : 'blue',
		color: 'white',
		weight: 1,
		opacity: 1,
		fillOpacity: 0.8,
	});

	const pointToLayer = (feature, latlng) => {
		return L.circleMarker(latlng, stylePoints(feature));
	};

	const SetViewOnLoad = ({ center, zoom }) => {
		const map = useMap();
		map.setView(center, zoom);
		return null;
	};

	async function getEvacuationPath(
		orig: string,
		dest: string,
		exclusions: string
	) {
		try {
			const response = await axios.get('http://localhost:8100/shortest_path', {
				params: {
					orig: orig,
					dest: dest,
					exclusions: exclusions,
				},
				headers: { 'Content-Type': 'application/json' },
			});
			setEvacuationPath(response.data);
		} catch (error: any) {
			console.error(error.response);
			console.log('Issue getting evacuation path');
		}
	}
	useEffect(() => {
		if (userDestination != '') {
			getEvacuationPath(userStartLocation, userDestination, '');
		}
	}, [userDestination]);

	return (
		<ThemeProvider theme={theme}>
			<div className='App'>
				<header className='App-header'></header>
				<div
					sx={{
						width: '100vw',
						height: '100vh',
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
					}}>
					<Paper
						sx={{
							padding: '1%',
							width: '30%',
							maxWidth: '500px',
							maxHeight: '700px',
							position: 'absolute',
							left: 0,
							bottom: 0,
							zIndex: 1000,
							overflowY: 'auto', // Allow scrolling when content exceeds max height
						}}
						elevation={2}>
						<div sx={{ display: 'flex', flexDirection: 'column' }}>
							{/* Chat history messages */}
							{chatHistory.map((message) =>
								message.displayName === 'User' ? (
									<MessageLeft key={crypto.randomUUID()} {...message} />
								) : (
									<MessageRight key={crypto.randomUUID()} {...message} />
								)
							)}

							{/* Text input for user questions */}
							<div>
								<TextInput
									value={userQuestion}
									onTextChange={(e) => setUserQuestion(e.target.value)}
									inputHandler={handleQuestionSubmit}
								/>
							</div>
						</div>
					</Paper>
				</div>
				<MapContainer
					center={[40.703, -74.017]} // Initial center point (Battery, NY)
					zoom={6} // Initial zoom level
					style={{ height: '100vh', width: '100%' }}>
					<TileLayer
						url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
						attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
					/>
					{display311Data && geoJSONData311 && (
						// <GeoJSON
						// 	data={geoJSONData311}
						// 	pointToLayer={pointToLayer}
						// 	onEachFeature={onEachFeature}
						// />
						<Polygon positions={geoJSONData311} color='blue' />
					)}
					{evacuationPath && <GeoJSON data={evacuationPath} />}
					<SetViewOnLoad center={[40.7486538125, -73.98530431249999]} zoom={14} />
				</MapContainer>
			</div>
		</ThemeProvider>
	);
}

export default App;
